import time
from umqtt_simple import MQTTClient
import machine
import network
import urequests

name = "setup_board"

# MQTT broker 
broker_ip = 'broker.tplinkdns.com'
#broker_ip = '192.168.0.152'

# WiFi credentials
WIFI_SSID = 'AL.TAHHAN_5G'
WIFI_PASSWORD = 'altahhan2021'

subscribe = {
"update" : f"boards/{name}/cmd/update",
}

# Global variables for connection management
client = None
ping_timer = time.time()
connection_established = False

#Attempts to connect to wifi
def setup_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    # performance mode (less power-save jitter)
    try:
        wlan.config(pm=0xa11140)
    except:
        pass

    if wlan.isconnected():
        return True

    # hard reset Wi‑Fi state before new attempt
    try:
        wlan.disconnect()
    except:
        pass
    wlan.active(False)
    time.sleep_ms(200)
    wlan.active(True)

    print('Connecting to WiFi:', WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    for _ in range(30):  # ~30s
        if wlan.isconnected():
            print('WiFi connected:', wlan.ifconfig())
            return True
        time.sleep_ms(1000)
    print('WiFi failed')
    return False

#Attempts to connect to the MQTT client and subscibes to required topics
def setup_mqtt():
    """Setup MQTT connection with error handling"""
    global client, bp, connection_established
    
    try:
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        client = MQTTClient(name, broker_ip, keepalive=15)
        client.set_last_will(topic=f"boards/{name}/status", msg="OFFLINE", retain=True, qos=0)
        client.set_callback(on_callback)
        client.connect()
        
        # Subscribe to topics
        for topic in subscribe:
            try:
                client.subscribe(subscribe[topic].encode())
            except Exception as e:
                print(f"Failed to subscribe to {topic}: {e}")
                
        connection_established = True
        
        print("MQTT connected successfully")
        return True
        
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        client = None
        return False

#Used to update files locally over the internet
def ota_update():
    try:
        file_list_url = f"http://broker.tplinkdns.com:80/file_list.txt"
        res = urequests.get(file_list_url)
        file_list = res.text.strip().splitlines()
        res.close()

        for filename in file_list:
            print(f"Updating {filename}...")
            res = urequests.get(f"http://broker.tplinkdns.com:80/{filename}")
            with open(filename, "w") as f:
                f.write(res.text)
            res.close()
        
        print("Update complete. Rebooting...")
        machine.reset()
    except Exception as e:
        print("OTA failed:", e)
        client.publish("error", f"{e}")

#Called whenever a topic the client is subscribed to gets a new message
def on_callback(topic, msg):
    try:
        print("Received: ", topic.decode(), msg.decode())
        
        topic = topic.decode()
        msg = msg.decode()
        if topic == subscribe["update"]:
            if msg == 'update':
                ota_update()
            
    except Exception as e:
        print(f"Error in callback: {e}")
        client.publish("error", f"{e}")

#Main Loop
def main_loop():
    """Main program loop with connection monitoring"""
    global ping_timer, connection_established, client, bp
    
    print("Starting main loop...")    
    while True: 
        try:
            if connection_established and client:
                
                current_time = time.time()
                if current_time - ping_timer > 15:
                    try:
                        client.publish("setup/board", "ONLINE", retain=True)
                        client.ping()
                        ping_timer = current_time
                    except Exception as e:
                        print(f"Ping failed: {e}")
                        bp.publish_error(e)
                        client = None
                
                # Check for MQTT messages
                try:
                    client.check_msg()
                except Exception as e:
                    print(f"MQTT check_msg error: {e}")
                    bp.publish_error(e)
                    client = None
            else:
                setup_wifi()
                setup_mqtt()
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            client.publish("error", f"{e}")
            # Continue running even if there's an error
            time.sleep(1)

# Initial setup
print("ESP32 Industrial Controller Starting...")
print("Attempting Initial Connection")
setup_wifi()
setup_mqtt()
# Start the main loop
main_loop()