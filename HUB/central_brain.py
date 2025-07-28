import paho.mqtt.client as mqtt
import time
from database_class import Database as DB
import datetime
import threading


db = DB("MQTT_System", "postgres", "altahhan2004!")
board_id_lookup = db.boardname_id_dict()
topic_id_lookup = db.topic_id_dict()

#defines a function thats triggered once when brain connects to broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("#")  # Subscribes to all machine topics

#function that gets triggered when a message gets published to subscribed topic
def on_message(client, userdata, msg):
    board_name = msg.topic.split("/")[1]
    board_id = board_lookup[board_name]
    message = msg.payload.decode()
    topic = msg.topic
    topic_id = topic_id_lookup[topic]

    db.id_insert_message(board_id, topic_id, message)
    
    if topic.endswith("/last_state"):
        db.update_last_state(message, board_id)

    if topic.endswith("/status"):
        db.update_status(message, board_id)
        if message == "ONLINE":
            client.publish(f"boards/{board_name}/cmd/last_state", db.get_last_state(board_id))
    
    if topic.endswith("/update_counter"):
        if message == "+1":
            db.increment_production_count(board_id)
            print (db.get_board_production_count(board_id))
        elif message == "-1":
            db.decrement_production_count(board_id)
            print (db.get_board_production_count(board_id))

    print(f"Received from {msg.topic}: {msg.payload.decode()}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
print("connected to client")



client.connect("localhost", 1883, 60)  # Localhost = your laptop



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




