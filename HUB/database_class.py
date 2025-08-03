import psycopg2
import time

class Database:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        #initializes connection to database
        self.conn = psycopg2.connect(
            dbname = dbname,
            user = user,
            password = password,
            host = host,
            port = port
            )

        #creates a cursor that points into the open database
        self.cursor = self.conn.cursor()

    def id_insert_message(self, board_id, topic_id, payload):
        #execute parameters (SQL commans in a string, values)
        self.cursor.execute(
            """
            INSERT INTO messages
            (publishing_board, message_topic, payload)
            VALUES (
            %s,%s,%s);
            """,
            (board_id,topic_id,payload)
            )

        #commits the changes to the database
        self.conn.commit()

    def name_insert_message(self,board_name, topic_name, payload):
        #uses the board and topic name to find respective ids and execute command
        self.cursor.execute(
            """
            INSERT INTO messages
            (publishing_board, message_topic, payload)
            VALUES(
            (SELECT b.id FROM esp32_boards b WHERE b.esp_name = %s),
            (SELECT t.id FROM topics t WHERE t.topic = %s),
            %s
            );"""
            , (board_name, topic_name, payload))
        self.conn.commit()

    def update_cylinder_count(self, board_id, cylinder_count):
        self.cursor.execute(
            """
            INSERT INTO production_log (board_id, log_date, cylinder_count)
            VALUES (%s, %s, %s);
            """
            , (board_id, time.time(), cylinder_count))
        self.conn.commit()

    def increment_production_count(self, board_id, cylinder_count, cylinder_size):
        # Construct dynamic SQL for the specific cylinder size column
        column_name = cylinder_size
        
        # Validate that the column exists
        self.cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'production_log' AND column_name = %s;
            """, (column_name,)
        )
        
        if not self.cursor.fetchone():
            print(f"Warning: Column '{column_name}' does not exist in production_log table")
            # Fallback to just updating cylinder_count
            self.cursor.execute(
                """
                INSERT INTO production_log (board_id, log_date, cylinder_count)
                VALUES (%s, CURRENT_DATE, 1)
                ON CONFLICT (board_id, log_date)
                DO UPDATE SET cylinder_count = production_log.cylinder_count + %s;
                """, (board_id, cylinder_count)
            )
        else:
            # Column exists, update both cylinder_count and the specific size column
            self.cursor.execute(
                """
                INSERT INTO production_log (board_id, log_date, cylinder_count)
                VALUES (%s, CURRENT_DATE, 1)
                ON CONFLICT (board_id, log_date)
                DO UPDATE SET 
                    cylinder_count = production_log.cylinder_count + %s,
                    "{}" = production_log."{}" + %s;
                """.format(column_name, column_name), 
                (board_id, cylinder_count, cylinder_count)
            )
        
        self.conn.commit()

    def decrement_production_count(self, board_id):
        self.cursor.execute(
            """
            INSERT INTO production_log (board_id, log_date, cylinder_count)
            VALUES (%s, CURRENT_DATE, 0)
            ON CONFLICT (board_id, log_date)
            DO UPDATE SET cylinder_count = GREATEST(production_log.cylinder_count - 1, 0);
            """, (board_id,))
        self.conn.commit()

    #Used once per day. Purpose is to keep track of boards that didnt detect anything on a given day
    def create_daily_log_entries(self):
        self.cursor.execute(
            """
            INSERT INTO production_log (board_id, log_date, cylinder_count)
            SELECT b.id, CURRENT_DATE, 0
            FROM esp32_boards b
            WHERE NOT EXISTS(SELECT 1 FROM production_log p
            WHERE p.board_id = b.id AND p.log_date = CURRENT_DATE
            );
            """)
        self.conn.commit()

    def get_board_production_count(self, board_id):
        self.cursor.execute("""SELECT cylinder_count FROM production_log p
            WHERE p.board_id = %s AND p.log_date = CURRENT_DATE;""", (board_id,))
        return self.cursor.fetchone()[0]

    def boardname_id_dict(self):
        self.cursor.execute(
            """
            SELECT esp_name, id FROM esp32_boards;
            """)
        data_list = self.cursor.fetchall()
        dic = {}
        for element in data_list:
            dic[element[0]] = element[1]
        return dic

    def topic_id_dict(self):
        self.cursor.execute(
            """
            SELECT topic, id FROM topics;
            """
            )
        data_list = self.cursor.fetchall()
        dic = {}
        for element in data_list:
            dic[element[0]] = element[1]
        return dic

        
    def update_last_state(self, last_state, board_id):
        self.cursor.execute(
            """
            UPDATE esp32_boards
            SET last_state = %s
            WHERE id = %s;""", (last_state, board_id)
            )
        self.conn.commit()

    def update_status(self, status, board_id):
        self.cursor.execute(
            """
            Update esp32_boards
            SET state = %s
            WHERE id = %s;
            """, (status, board_id)
            )
        self.conn.commit()

    def get_last_state(self, board_id):
        self.cursor.execute(
            """
            SELECT last_state
            FROM esp32_boards
            WHERE id = %s
            """, (board_id,)
            )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def insert_topic(self, topic_name):
        self.cursor.execute(
            """
            INSERT INTO topics (topic)
            VALUES (%s)
            ON CONFLICT (topic)
            DO NOTHING;
            """, (topic_name,)
            )
        self.conn.commit()

# Example usage (commented out):
# from config import config
# db_config = config.get_db_config()
# db = Database(**db_config)
# db.boardname_id_dict()
# db.name_insert_message("esp32_001", "factory/machine1/status", "online")
