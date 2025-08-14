import paho.mqtt.client as mqtt
import time
#from database_class import Database as DB
from database_supabase import Database as DB
import datetime
import threading
import os
from dotenv import load_dotenv
from config import config

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")

load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"URL from getenv: {url}")
print(f"Key from getenv: {key}")

if not url or not key:
    print("WTF IS HAPPENING")
    # Additional debugging
    print("All environment variables:")
    for k, v in os.environ.items():
        print(f"{k}: {v}")

try:
    #db_config = config.get_db_config()
    db = DB(url= url,key= key)
    board_id_lookup = db.boardname_id_dict()
    topic_id_lookup = db.topic_id_dict()
except Exception as e:
    print(f"Failed to initialize database connection: {e}")
    exit(1)
print(board_id_lookup)
print(topic_id_lookup)


#defines a function thats triggered once when brain connects to broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("#")  # Subscribes to all machine topics

#function that gets triggered when a message gets published to subscribed topic
def on_message(client, userdata, msg):
    global topic_id_lookup  # Declare as global to modify it
    
    try:
        board_name = msg.topic.split("/")[1]
        if board_name not in board_id_lookup:
            print(f"Unknown board: {board_name}")
            return
        
        board_id = board_id_lookup[board_name]
        message = msg.payload.decode()
        topic = msg.topic
        print (f"Recieved message: {message} from board: {board_name} {board_id}")
        if topic not in topic_id_lookup:
            db.insert_topic(topic)
            topic_id_lookup = db.topic_id_dict()  # Now properly updates the global variable
            
        topic_id = topic_id_lookup[topic]

        db.id_insert_message(board_id, topic_id, message)
        
        if topic.endswith("/last_state"):
            db.update_last_state(message, board_id)

        if topic.endswith("/status"):
            db.update_status(message, board_id)
            if message == "ONLINE":
                last_state = db.get_last_state(board_id)
                if last_state:
                    client.publish(f"boards/{board_name}/cmd/last_state", last_state)
        
        if topic.endswith("/update_counter"):
            counter_message = message.split(" ")
            cylinder_count = counter_message[0]
            cylinder_size = counter_message[1]
            if cylinder_count[0] == "+":
                db.increment_production_count(board_id, int(cylinder_count[1:]), cylinder_size)
                production_count = db.get_board_production_count(board_id)
                if production_count is not None:
                    print(production_count)
            elif cylinder_count[0] == "-":
                db.decrement_production_count(board_id)
                production_count = db.get_board_production_count(board_id)
                if production_count is not None:
                    print(production_count)

        print(f"Received from {msg.topic}: {msg.payload.decode()}")
        
    except Exception as e:
        print(f"Error processing message from {msg.topic}: {e}")


while True:
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        mqtt_config = config.get_mqtt_config()
        client.connect(mqtt_config['host'], mqtt_config['port'], mqtt_config['keepalive'])
        print("connected to client")
        break
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        print("Trying again in 5 seconds..")
        time.sleep(5)






def time_based_publisher():
    daily_start = False
    while True:
        now = datetime.datetime.now()
        if now.hour == 7 and 0 < now.minute < 30 and not daily_start:
            # Replace with your actual topic and message
            client.publish("boards/cmd/reset_counter", "Morning Reset", retain=True)
            daily_start = True
            time.sleep(60)  # wait 60 seconds to avoid spamming
        time.sleep(1)  # check every second


threading.Thread(target=time_based_publisher, daemon=True).start()
client.loop_forever()




