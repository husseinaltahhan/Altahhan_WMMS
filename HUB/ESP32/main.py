import time
from machine import Pin
from umqtt_simple import MQTTClient
import machine
import urequests
from publisher import BoardPublisher
from sensor import SensorDetections

name = "esp32_b1"

# MQTT broker 
broker_ip = '192.168.68.102'


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
client = MQTTClient("esp32_client", broker_ip) #names the client and uses the broker_ip to connect
client.set_last_will(topic=f"boards/{name}/status", msg="OFFLINE", retain=True, qos=0)
client.connect()


#creatubg an instance of the publishing class to communicate with broker
bp = BoardPublisher(client)
bp.publish_status("ONLINE")

sd = SensorDetections(13,14,34)

#Used to update files locally over the internet
def ota_update():
    try:
        file_list_url = "http://192.168.68.102:80/file_list.txt"
        res = urequests.get(file_list_url)
        file_list = res.text.strip().splitlines()
        res.close()

        for filename in file_list:
            print (f"Updating {filename}...")
            res = urequests.get(f"http://192.168.68.102:80/{filename}")
            with open(filename, "w") as f:
                f.write(res.text)
            res.close()
        
        print("Update complete. Rebooting...")
        machine.reset()
    except Exception as e:
        print("OTA failed:", e)


#called whenever a topic the client is subscribed to gets a new message
def on_callback(topic, msg):
    if topic == subscribe["status"]:
        if msg == b'stop':
            print ("stopping")
    if topic == subscribe["update"]:
        if msg == b'update':
            ota_update()

    if topic == subscribe["last_state"]:
        sd.state_update(msg)
 
client.set_callback(on_callback) #sets the function created as the defult callback function


#subscribes to necessary topics
for topic in subscribe:
    client.subscribe(subscribe[topic]))


# Stay connected and loop forever
while True:
    sd.sensor_detect(bp)

    #checks for any new messages every 2 seconds
    client.check_msg()
    time.sleep_ms(10)
