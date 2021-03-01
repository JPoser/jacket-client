import network
import ujson
import urequests
import neopixel 
import machine
import time

print('initialising network')
# turn on and connect to wifi
def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('', '')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

do_connect()
n = 21
p = 2
np = neopixel.NeoPixel(machine.Pin(p), n)

while True:
    response = urequests.get('http://herbert:5000/api/v1.0/get_tweets')
    response = ujson.loads(response.text)
    print(response)
    if response['colour'] == 'blue':
        np[0] = (0, 0, 255)
        np.write()
    elif response['colour'] == 'red':
        np[0] = (255, 0, 0)
        np.write()
    elif response['colour'] == 'green':
        np[0] = (0, 255, 0)
        np.write(0)
    time.sleep(5)
