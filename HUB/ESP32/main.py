import time
from machine import Pin
from umqtt_simple import MQTTClient
import machine
import urequests
from publisher import BoardPublisher
from dt_method_1 import SensorDetections

name = "esp32_b1"

# MQTT broker 
broker_ip = '192.168.68.109'


subscribe = {
"reset_all" : b"boards/cmd/reset_counter",
"reset" : b"boards/esp32_b1/cmd/reset_counter",
"reboot_all" : b"boards/cmd/reboot",
"reboot" : b"boards/esp32_b1/cmd/reboot",
"update" : b"boards/esp32_b1/cmd/update",
"update_all" : b"boards/cmd/update",
"status" : b"boards/esp32_b1/cmd/status",
"last_state" : b"boards/esp32_b1/cmd/last_state"
}


# Connect to MQTT broker
client = MQTTClient("esp32_client", broker_ip, keepalive=15) #names the client and uses the broker_ip to connect
client.set_last_will(topic=f"boards/{name}/status", msg="OFFLINE", retain=True, qos=0)
ping_timer = time.time()
client.connect()


#creatubg an instance of the publishing class to communicate with broker
bp = BoardPublisher(client)

sd = SensorDetections(25,32,13)

#Used to update files locally over the internet
def ota_update():
    try:
        file_list_url = "http://192.168.68.101:80/file_list.txt"
        res = urequests.get(file_list_url)
        file_list = res.text.strip().splitlines()
        res.close()

        for filename in file_list:
            print (f"Updating {filename}...")
            res = urequests.get(f"http://192.168.68.101:80/{filename}")
            with open(filename, "w") as f:
                f.write(res.text)
            res.close()
        
        print("Update complete. Rebooting...")
        machine.reset()
    except Exception as e:
        print("OTA failed:", e)


#called whenever a topic the client is subscribed to gets a new message
def on_callback(topic, msg):
    print("Recieved: ", topic.decode(), msg.decode())
    if topic == subscribe["status"]:
        if msg == b'stop':
            print ("stopping")
    if topic == subscribe["update"]:
        if msg == b'update':
            ota_update()

    if topic == subscribe["last_state"]:
        print(msg.decode())
        sd.state_update(msg.decode())


def is_wifi_connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()

def reconnect_wifi():
    ssid = 'AL .TAHHAN_5G'
    password = 'altahhan2021'

    station = network.WLAN(network.STA_IF)  # Create station interface
    station.active(True)                    # Activate the interface

    station.connect(ssid, password)         # Connect to Wi-Fi

    # Wait for connection with timeout
    timeout = 10
    while timeout > 0:
        if station.isconnected():
            break
        print('Connecting...')
        timeout -= 1
        time.sleep(1)

        if station.isconnected():
            print('Connected to WiFi')
            print('Network config:', station.ifconfig())
        else:
            print('Failed to connect')

def reconnect_mqtt():
    client = MQTTClient("esp32_client", broker_ip, keepalive=10) #names the client and uses the broker_ip to connect
    client.set_last_will(topic=f"boards/{name}/status", msg="OFFLINE", retain=True, qos=0)
    client.connect()

def reconnect():
    reconnect_timer = time.time()
    while True:
        if not is_wifi_connected():
            reconnect_wifi()
            continue  # retry Wi-Fi first, then MQTT once Wi-Fi is up

        try:
            reconnect_mqtt()
            print("Reconnected successfully.")
            break  # Success!
        except Exception as e:
            print("MQTT reconnect failed:", e)

        if (time.time() - reconnect_timer) > 10:
            print("Failed to reconnect after 10 seconds.")
            break
        time.sleep(1)  # wait 1s before retrying to avoid tight loop
        
 
client.set_callback(on_callback) #sets the function created as the defult callback function


#subscribes to necessary topics
for topic in subscribe:
    client.subscribe(subscribe[topic])
bp.publish_status("ONLINE")

# Stay connected and loop forever
while True:
    sd.sensor_detect(bp)
    if time.time() - ping_timer > 5:
        client.ping()
        ping_timer = time.time()

    #checks for any new messages every 2 seconds

    try:
        client.check_msg()
    except OSError as e:
        print("MQTT error, reconnecting...", e)
        reconnect()
        
    time.sleep_ms(10)


