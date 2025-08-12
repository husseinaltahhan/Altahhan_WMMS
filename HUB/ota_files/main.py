import time
from machine import Pin
from umqtt_simple import MQTTClient
import machine
import network
import urequests
import _thread
from publisher import BoardPublisher
from dt_method_2 import GateWeldingDetector

name = "esp32_b1"

# MQTT broker 
broker_ip = 'broker.tplinkdns.com'
#broker_ip = '192.168.0.152'

# WiFi credentials
WIFI_SSID = 'WMMS'
WIFI_PASSWORD = 'Altahhan2004!'

# WiFi credentials
#WIFI_SSID = 'AL.TAHHAN_5G'
#WIFI_PASSWORD = 'altahhan2021'

subscribe = {
"reset_all" : f"boards/cmd/reset_counter",
"reset" : f"boards/{name}/cmd/reset_counter",
"reboot_all" : f"boards/cmd/reboot",
"reboot" : f"boards/{name}/cmd/reboot",
"update" : f"boards/{name}/cmd/update",
"update_all" : f"boards/cmd/update",
"status" : f"boards/{name}/cmd/status",
"last_state" : f"boards/{name}/cmd/last_state"
}

# Global variables for connection management
client = None
bp = BoardPublisher()  # Create publisher without client initially
gd = GateWeldingDetector(18, 21)
ping_timer = time.time()
connection_established = False
_reconnect_running = False

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
        
        # Update publisher with new client
        bp.set_client(client)
        bp.publish_status("ONLINE")
        
        connection_established = True
        
        print("MQTT connected successfully")
        return True
        
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        bp.publish_error(e)
        client = None
        bp.set_connection_status(False)
        return False

#Checks if wifi is connected
def is_wifi_connected():
    """Check if WiFi is connected"""
    
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return True
    else:
        return False

#Checks if MQTT client is connected
def is_mqtt_connected():
    """Check if MQTT is connected"""
    global client
    if client is None:
        return False
    else:
        return True

#Main Function Responsible for Reconnection Runs both setup_wifi and setup_mqtt
def attempt_reconnection():
    global _reconnect_running, connection_established, client
    
    if _reconnect_running:
        return
    _reconnect_running = True
    try:
        while not is_wifi_connected() or not is_mqtt_connected():
            if not is_wifi_connected():
                print ("Attempting Wifi Reconnection..")
                setup_wifi()
            elif not is_mqtt_connected():
                print ("Attempting MQTT Reconnection..")
                setup_mqtt()
            time.sleep(3)
        connection_established = True
        print('Reconnection successful!')
    
    finally:
        _reconnect_running = False

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
        bp.publish_error(e)

#Called whenever a topic the client is subscribed to gets a new message
def on_callback(topic, msg):
    try:
        print("Received: ", topic.decode(), msg.decode())
        
        topic = topic.decode()
        msg = msg.decode()
        
        if topic == subscribe["status"]:
            if msg == 'stop':
                print("stopping")
        
        if topic == subscribe["update"]:
            if msg == 'update':
                ota_update()

        if topic == subscribe["last_state"]:
            print(msg)
            gd.state_update(msg)
            
        if topic == subscribe["reset_all"]:
            gd.state_update("IDLE 0 0 False")
            
        if topic == subscribe["reboot"]:
            machine.reset()
            
    except Exception as e:
        print(f"Error in callback: {e}")
        bp.publish_error(e)

#Main Loop
def main_loop():
    """Main program loop with connection monitoring"""
    global ping_timer, connection_established, client, bp
    
    print("Starting main loop...")
    connection_established = True
    
    while True: 
        try:
            # Check connections and attempt reconnection if needed
            if not is_wifi_connected() or not is_mqtt_connected():
                if connection_established:
                    connection_established = False
                    bp.set_connection_status(False)
                    _thread.start_new_thread(attempt_reconnection, ())
            
            # Always run sensor detection regardless of connection status
            gd.sensor_detect(bp)
            
            # Handle MQTT operations only if connected
            if connection_established and client:
                # Update publisher connection status
                bp.set_connection_status(True)
                # Handle MQTT ping
                current_time = time.time()
                if current_time - ping_timer > 5:
                    try:
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
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            bp.publish_error(e)
            # Continue running even if there's an error
            time.sleep(1)

# Initial setup
print("ESP32 Industrial Controller Starting...")
print("Attempting Initial Connection")
setup_wifi()
setup_mqtt()
# Start the main loop
main_loop()