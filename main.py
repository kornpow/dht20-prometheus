# from microdot import Microdot
import network
from microdot_asyncio import Microdot
from picozero import pico_temp_sensor, pico_led
from time import sleep
import urandom
import json
import uasyncio as asyncio


from machine import Pin, I2C, WDT
from utime import sleep


from dht20 import DHT20
from prometheus_express import check_network, start_http_server, CollectorRegistry, Counter, Gauge, Router

registry = CollectorRegistry(namespace="pico_dht20")

i2c0_sda = Pin(4)
i2c0_scl = Pin(5)
i2c0 = I2C(0, sda=i2c0_sda, scl=i2c0_scl)

from dht20 import DHT20
dht20 = DHT20(0x38, i2c0)

app = Microdot()

humidity_g = Gauge(
    'humidity_gauge',
    'humidity sensor gauge',
    labels=['ip'],
    registry=registry
)

temp_g = Gauge(
    'temp_gauge',
    'temp sensor gauge',
    labels=['ip'],
    registry=registry
)

tempf_g = Gauge(
    'temp_gauge',
    'temp sensor gauge fahrenheight',
    labels=['ip'],
    registry=registry
)

wifi_rssi_g = Gauge(
    'wifi_rssi_gauge',
    'wifi_signal_rssi',
    labels=['ip'],
    registry=registry
)

async def scheduled_task(interval):
    while True:
        # Your task here
        print("Running scheduled task")
        
        signal_strength = wlan.status('rssi')
        if wlan.isconnected():
            print(f"WiFi is connected. rssi: {signal_strength}. Resseting watchdog")
            wdt.feed()
        else:
            print("WiFi is disconnected")
        # Sleep for the specified interval
        await asyncio.sleep(interval)

def random_between(min_val, max_val):
    return min_val + urandom.getrandbits(7) * (max_val - min_val + 1) // 128


@app.route("/metrics")
async def metrics(request):
    print("metrics")
    signal_strength = wlan.status('rssi')
    measurements = dht20.measurements
    temp_g.set(measurements["t"])
    humidity_g.set(measurements["rh"])
    wifi_rssi_g.set(signal_strength)
    metrics = "\n".join(registry.render())
    #print(metrics)
    return metrics, 200
    

@app.route('/')
async def index(request):
    pico_led.off()
    sleep(0.5)
    pico_led.on()
    measurements = dht20.measurements
    signal_strength = wlan.status('rssi')
    print(measurements)
    print(f"Temperature: {measurements['t']} °C, humidity: {measurements['rh']} %RH")
    data = {
        "tempC": measurements["t"],
        "humidity": measurements["rh"],
        "signal": signal_strength
    }
    return json.dumps(data)

wlan = network.WLAN(network.STA_IF)


async def connect_network():
    wlan.active(True)
    print(wlan.scan())
    net = wlan.connect(ssid="kibiru-5", key="soorin93")
    print(net)
    print(wlan.status())
    retry_count = 0
    while not wlan.isconnected():
        print(f"not yet connected: {retry_count}")
        pico_led.on()
        sleep(0.5)
        pico_led.off()
        sleep(0.5)
        retry_count += 1
    print(wlan.isconnected())
    print("running!")
    pico_led.on()

async def webserver():
    await asyncio.run(app.run(port=8080))
    
async def main():
    asyncio.create_task(scheduled_task(2))
    asyncio.create_task(connect_network())  # Run the background_task every 5 seconds
    await webserver()  # Run the main_task

wdt = WDT(timeout=8000)
# Run the main function
asyncio.run(main())

# local AP
#ap = network.WLAN(network.AP_IF)
# connect to remote AP
#wlan = network.WLAN(network.STA_IF)