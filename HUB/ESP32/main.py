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
broker_ip = '192.168.68.103'

# WiFi credentials
WIFI_SSID = 'AL .TAHHAN_5G'
WIFI_PASSWORD = 'altahhan2021'

subscribe = {
"reset_all" : b"boards/cmd/reset_counter",
"reset" : b"boards/{name}/cmd/reset_counter",
"reboot_all" : b"boards/cmd/reboot",
"reboot" : b"boards/{name}/cmd/reboot",
"update" : b"boards/{name}/cmd/update",
"update_all" : b"boards/cmd/update",
"status" : b"boards/{name}/cmd/status",
"last_state" : b"boards/{name}/cmd/last_state"
}

# Global variables for connection management
client = None
bp = BoardPublisher()  # Create publisher without client initially
gd = GateWeldingDetector(18, 14)
ping_timer = time.time()
connection_established = False

#Attempts to connect to wifi
def setup_wifi():
    """Setup WiFi connection with retry logic"""
    global connection_established
    
    station = network.WLAN(network.STA_IF)
    station.active(True)
    
    if station.isconnected():
        print('WiFi already connected')
        return True
    
    print(f'Connecting to WiFi: {WIFI_SSID}')
    station.connect(WIFI_SSID, WIFI_PASSWORD)
    
    # Wait for connection with timeout
    timeout = 15
    while timeout > 0 and not station.isconnected():
        print('Connecting to WiFi...')
        timeout -= 1
        time.sleep(1)
    
    if station.isconnected():
        print('WiFi connected successfully')
        print('Network config:', station.ifconfig())
        return True
    else:
        print('Failed to connect to WiFi')
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
                client.subscribe(subscribe[topic])
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
    """Attempt to reconnect WiFi and MQTT"""
    global connection_established
    
    print("Attempting reconnection...")
    
    while not is_wifi_connected() or not is_mqtt_connected():
        # First ensure WiFi is connected
        if not is_wifi_connected():
            print("WiFi disconnected, attempting reconnection...")
            setup_wifi()
        
        # Then ensure MQTT is connected
        elif not is_mqtt_connected():
            print("MQTT disconnected, attempting reconnection...")
            setup_mqtt()
        
        time.sleep(5)
    
    connection_established = True
    print("Reconnection successful!")

#Used to update files locally over the internet
def ota_update():
    try:
        file_list_url = f"http://{broker_ip}:80/file_list.txt"
        res = urequests.get(file_list_url)
        file_list = res.text.strip().splitlines()
        res.close()

        for filename in file_list:
            print(f"Updating {filename}...")
            res = urequests.get(f"http://{broker_ip}:80/{filename}")
            with open(filename, "w") as f:
                f.write(res.text)
            res.close()
        
        print("Update complete. Rebooting...")
        machine.reset()
    except Exception as e:
        print("OTA failed:", e)

#Called whenever a topic the client is subscribed to gets a new message
def on_callback(topic, msg):
    try:
        print("Received: ", topic.decode(), msg.decode())
        
        if topic == subscribe["status"]:
            if msg == b'stop':
                print("stopping")
        
        if topic == subscribe["update"]:
            if msg == b'update':
                ota_update()

        if topic == subscribe["last_state"]:
            print(msg.decode())
            gd.state_update(msg.decode())
            
        if topic == subscribe["reset_all"]:
            gd.state_update("IDLE 0 0 False")
            
        if topic == subscribe["reboot"]:
            machine.reset()
            
    except Exception as e:
        print(f"Error in callback: {e}")

#Main Loop
def main_loop():
    """Main program loop with connection monitoring"""
    global ping_timer, connection_established, client, bp
    
    print("Starting main loop...")
    
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
                        client = None
                
                # Check for MQTT messages
                try:
                    client.check_msg()
                except Exception as e:
                    print(f"MQTT check_msg error: {e}")
                    client = None
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            # Continue running even if there's an error
            time.sleep(1)

# Initial setup
print("ESP32 Industrial Controller Starting...")

# Start the main loop
main_loop()