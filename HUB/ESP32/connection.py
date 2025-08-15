
import network, time, machine
from umqtt_simple import MQTTClient


class Connector():
    def __init__(self, name, detection=None, publisher=None):
        self.name = name
        
        self.detection = detection
        self.publisher = publisher
        
        # MQTT broker 
        self.broker_ip = 'broker.tplinkdns.com'
        #broker_ip = '192.168.0.152'
        
        # WiFi credentials
        self.WIFI_SSID = 'WMMS'
        self.WIFI_PASSWORD = 'Altahhan2004!'
        
        self.subscribe = {
        "reset_all" : f"boards/cmd/reset_counter",
        "reset" : f"boards/{name}/cmd/reset_counter",
        "reboot_all" : f"boards/cmd/reboot",
        "reboot" : f"boards/{name}/cmd/reboot",
        "update" : f"boards/{name}/cmd/update",
        "update_all" : f"boards/cmd/update",
        "status" : f"boards/{name}/cmd/status",
        "last_state" : f"boards/{name}/cmd/last_state"
        }
        
        self.client = None
        self.connection_established = True
        self.reconnect_running = False
        
        self.ping_timer = time.time()
        
    def set_detection(self, detector):
        self.detection = detector    
    
    def set_publisher(self, publisher):
        self.publisher = publisher
    
    def connect_wifi(self):
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

        print('Connecting to WiFi:', self.WIFI_SSID)
        wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
        
        for _ in range(30):  # ~30s
            if wlan.isconnected():
                print('WiFi connected:', wlan.ifconfig())
                return True
            time.sleep_ms(1000)
        print('WiFi failed')
        return False
    
    def connect_mqtt(self):
        """Setup MQTT connection with error handling""" 
          
        try:
            publisher = self.publisher
            if self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
            
            self.client = MQTTClient(self.name, self.broker_ip, keepalive=15)
            self.client.set_last_will(topic=f"boards/{self.name}/status", msg="OFFLINE", retain=True, qos=0)
            self.client.set_callback(self.on_callback)
            self.client.connect()
            
            # Subscribe to topics
            for topic in self.subscribe:
                try:
                    self.client.subscribe(self.subscribe[topic].encode())
                except Exception as e:
                    print(f"Failed to subscribe to {topic}: {e}")
            
            # Update publisher with new client
            publisher.set_client(self.client)
            publisher.publish_status("ONLINE")
            
            connection_established = True
            
            print("MQTT connected successfully")
            return True
            
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            publisher.publish_error(e)
            self.client = None
            publisher.set_connection_status(False)
            return False
    
    def on_callback(self, topic, msg):
        try:
            subscribe = self.subscribe
            topic = topic.decode()
            msg = msg.decode()
            
            print("Received: ", topic, msg)

            
            if topic == subscribe["status"]:
                if msg == 'stop':
                    print("stopping")
            
            if topic == subscribe["update"]:
                if msg == 'update':
                    ota_update()

            if topic == subscribe["last_state"]:
                print(msg)
                self.detection.state_update(msg)
                
            if topic == subscribe["reset_all"]:
                self.detection.state_update("IDLE 0 0 False")
                
            if topic == subscribe["reboot"]:
                machine.reset()
                
        except Exception as e:
            print(f"Error in callback: {e}")
            self.publisher.publish_error(e)
      
    def is_wifi_connected(self):
        """Check if WiFi is connected"""
        
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            return True
        else:
            return False
    
    def is_mqtt_connected(self):
        """Check if MQTT is connected"""
        if self.client is None:
            return False
        else:
            return True
        
    def attempt_reconnection(self):
        _reconnect_running = self.reconnect_running
        
        if _reconnect_running:
            return
        _reconnect_running = True
        try:
            while not self.is_wifi_connected() or not self.is_mqtt_connected():
                if not self.is_wifi_connected():
                    print ("Attempting Wifi Reconnection..")
                    self.connect_wifi()
                elif not self.is_mqtt_connected():
                    print ("Attempting MQTT Reconnection..")
                    self.connect_mqtt()
                time.sleep(3)
            self.connection_established = True
            print('Reconnection successful!')
        
        finally:
            _reconnect_running = False

    def run(self):
        
        client = self.client
        publisher = self.publisher
    
        try:
            # Check connections and attempt reconnection if needed
            if not self.is_wifi_connected() or not self.is_mqtt_connected():
                if self.connection_established:
                    self.connection_established = False
                    publisher.set_connection_status(False)
                    self.attempt_reconnection()
            
            # Handle MQTT operations only if connected
            if self.connection_established and client:
                # Update publisher connection status
                publisher.set_connection_status(True)
                # Handle MQTT ping
                current_time = time.time()
                if current_time - self.ping_timer > 5:
                    try:
                        client.ping()
                        self.ping_timer = current_time
                    except Exception as e:
                        print(f"Ping failed: {e}")
                        publisher.publish_error(e)
                        client = None
                
                # Check for MQTT messages
                try:
                    client.check_msg()
                except Exception as e:
                    print(f"MQTT check_msg error: {e}")
                    publisher.publish_error(e)
                    client = None
        except Exception as e:
            print(f"Error in main loop: {e}")
            publisher.publish_error(e)
            # Continue running even if there's an error
            time.sleep(1)