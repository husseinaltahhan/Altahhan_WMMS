import paho.mqtt.client as mqtt
import time
from database_class import Database as DB
import datetime
import threading
from config import config


try:
    db_config = config.get_db_config()
    db = DB(**db_config)
    board_id_lookup = db.boardname_id_dict()
    topic_id_lookup = db.topic_id_dict()
except Exception as e:
    print(f"Failed to initialize database connection: {e}")
    exit(1)

#defines a function thats triggered once when brain connects to broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("#")  # Subscribes to all machine topics

#function that gets triggered when a message gets published to subscribed topic
def on_message(client, userdata, msg):
    try:
        board_name = msg.topic.split("/")[1]
        if board_name not in board_id_lookup:
            print(f"Unknown board: {board_name}")
            return
            
        board_id = board_id_lookup[board_name]
        message = msg.payload.decode()
        topic = msg.topic
        
        if topic not in topic_id_lookup:
            print(f"Unknown topic: {topic}")
            return
            
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
            if message == "+1":
                db.increment_production_count(board_id)
                production_count = db.get_board_production_count(board_id)
                if production_count is not None:
                    print(production_count)
            elif message == "-1":
                db.decrement_production_count(board_id)
                production_count = db.get_board_production_count(board_id)
                if production_count is not None:
                    print(production_count)

        print(f"Received from {msg.topic}: {msg.payload.decode()}")
        
    except Exception as e:
        print(f"Error processing message from {msg.topic}: {e}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
print("connected to client")



mqtt_config = config.get_mqtt_config()
client.connect(mqtt_config['host'], mqtt_config['port'], mqtt_config['keepalive'])



def time_based_publisher():
    while True:
        now = datetime.datetime.now()
        if now.hour == 7 and now.minute == 0:
            # Replace with your actual topic and message
            client.publish("boards/cmd/reset_counter", "Morning Reset", retain=True)
            time.sleep(60)  # wait 60 seconds to avoid spamming
        time.sleep(1)  # check every second


threading.Thread(target=time_based_publisher, daemon=True).start()
client.loop_forever()




