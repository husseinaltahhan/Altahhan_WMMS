import psycopg2

# Step 1: Connect to the database
conn = psycopg2.connect(
    dbname="MQTT_System",
    user="postgres",
    password="altahhan2004!",
    host="localhost",  # or IP address of the Pi
    port="5432"
)

cursor = conn.cursor()

# Step 2: Write a safe INSERT statement
cursor.execute(
    """
    INSERT INTO messages (publishing_board, message_topic, payload)
    VALUES (%s, %s, %s)
    """,
    (1, 1, "ESP32 just went online")
)

# Step 3: Commit the changes and close
conn.commit()
cursor.close()
conn.close()
