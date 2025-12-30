import network
import urequests
import neopixel
import machine
import time
import gc
import config

# Global variables for state tracking
current_color = (0, 0, 0)
wlan = None
wdt = None


def init_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return wlan


def check_connection():
    """Check WiFi connection and reconnect if necessary."""
    global wlan, wdt
    if not wlan:
        init_wifi()

    if not wlan.isconnected():
        print('WiFi lost. Reconnecting...')
        try:
            wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            # Wait briefly for connection, feeding watchdog to prevent reset
            for _ in range(config.WIFI_RETRY_ATTEMPTS):
                if wdt:
                    wdt.feed()
                if wlan.isconnected():
                    print('Reconnected!')
                    return True
                time.sleep(1)
        except OSError as e:
            print(f"WiFi Error: {e}")
            return False

    return wlan.isconnected()


def update_leds(np, target_color):
    """Update LEDs only if color has changed."""
    global current_color
    if current_color != target_color:
        print(f"Updating LEDs to {target_color}")
        for i in range(config.LED_COUNT):
            np[i] = target_color
        np.write()
        current_color = target_color


def run():
    global wdt

    print('Starting Jacket Client (Robust Mode)...')

    # Initialize Watchdog Timer (30 second timeout)
    # Note: You must feed it periodically or the ESP32 will reset
    wdt = machine.WDT(timeout=30000)

    # Initialize NeoPixels
    np = neopixel.NeoPixel(machine.Pin(config.LED_PIN), config.LED_COUNT)

    # Startup indication - blue flash
    update_leds(np, config.COLOR_STARTUP)
    time.sleep(0.5)
    update_leds(np, config.COLOR_OFF)

    # Initial cleanup
    gc.collect()

    # Initialize and connect WiFi
    init_wifi()
    check_connection()

    url = f"{config.SERVER_URL}/api/v1/color"
    headers = {'X-API-Key': config.API_KEY}

    while True:
        # 1. Feed the Watchdog
        wdt.feed()

        # 2. Garbage Collection
        gc.collect()

        # 3. Check/Restore Connection
        if not check_connection():
            print("No network. Retrying in 5s...")
            update_leds(np, config.COLOR_ERROR_NETWORK)
            time.sleep(config.POLL_INTERVAL)
            continue

        # 4. Query Server
        response = None
        try:
            response = urequests.get(url, headers=headers, timeout=config.HTTP_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                if 'color' in data and 'rgb' in data['color']:
                    rgb = data['color']['rgb']
                    if len(rgb) == 3:
                        new_color = tuple(rgb)
                        update_leds(np, new_color)
            else:
                print(f"Server Error: {response.status_code}")
                update_leds(np, config.COLOR_ERROR_SERVER)

        except OSError as e:
            print(f"Network Request Failed: {e}")
            update_leds(np, config.COLOR_ERROR_NETWORK)

        except Exception as e:
            print(f"Unexpected Error: {e}")

        finally:
            if response:
                response.close()

        # Wait before next poll
        time.sleep(config.POLL_INTERVAL)


if __name__ == '__main__':
    run()
