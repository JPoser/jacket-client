# Configuration for Jacket Client

# WiFi Credentials
WIFI_SSID = 'your_wifi_ssid'
WIFI_PASSWORD = 'your_wifi_password'

# Server Configuration
SERVER_URL = 'http://192.168.1.100:5000'  # Replace with your server IP
API_KEY = 'your_api_key_here'            # Must match server config

# LED Configuration
LED_PIN = 2
STRIP_COUNT = 6
LEDS_PER_STRIP = 14
LED_COUNT = STRIP_COUNT * LEDS_PER_STRIP  # 84 total

# Status Colors (RGB tuples)
COLOR_ERROR_NETWORK = (50, 0, 0)      # Red - WiFi/network issues
COLOR_ERROR_SERVER = (50, 20, 0)      # Orange - server errors
COLOR_STARTUP = (0, 0, 50)            # Blue - booting up
COLOR_OFF = (0, 0, 0)                 # Off

# Timing Configuration (seconds)
POLL_INTERVAL = 5
HTTP_TIMEOUT = 10
WIFI_RETRY_ATTEMPTS = 10
