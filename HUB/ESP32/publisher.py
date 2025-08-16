import time

class BoardPublisher():
    def __init__(self, client=None):
        self.client = client
        self.message_queue = []
        self.max_queue_size = 100
        self.is_connected = False
        
    def set_client(self, client):
        """Set or update the MQTT client"""
        self.client = client
        self.is_connected = True
        # Send any queued messages when client is set
        self.send_queued_messages()
    
    def set_connection_status(self, status):
        """Update connection status"""
        self.is_connected = status
    
    def queue_message(self, message_type, topic, payload, retain=False):
        """Queue a message to be sent when connection is restored"""
        if len(self.message_queue) >= self.max_queue_size:
            # Remove oldest message to make room
            self.message_queue.pop(0)
            print("Message queue full, removing oldest message")
        
        self.message_queue.append({
            'type': message_type,
            'topic': topic,
            'payload': payload,
            'retain': retain,
            'timestamp': time.time()
        })
        print(f"Queued {message_type} message. Queue size: {len(self.message_queue)}")
    
    def send_queued_messages(self):
        """Send all queued messages when connection is restored"""
        if not self.client or not self.is_connected or len(self.message_queue) == 0:
            return
        
        print(f"Sending {len(self.message_queue)} queued messages...")
        messages_sent = 0
        
        # Create a copy of the queue and clear the original
        messages_to_send = self.message_queue.copy()
        self.message_queue.clear()
        
        for message in messages_to_send:
            try:
                self.client.publish(message['topic'], message['payload'], retain=message['retain'])
                messages_sent += 1
            except Exception as e:
                print(f"Failed to send queued message: {e}")
                # Re-queue the failed message
                self.message_queue.append(message)
        
        print(f"Successfully sent {messages_sent} queued messages")
    
    def safe_publish(self, topic, payload, retain=False, message_type="generic"):
        """Safely publish a message - queue if offline"""
        if self.is_connected and self.client:
            try:
                self.client.publish(topic, payload, retain=retain)
                return True
            except Exception as e:
                print(f"Publish failed, queuing message: {e}")
                self.is_connected = False
                self.queue_message(message_type, topic, payload, retain)
                return False
        else:
            self.queue_message(message_type, topic, payload, retain)
            return False

    def publish_counter(self, count, size):
        self.safe_publish(
            topic=b"boards/esp32_b1/update_counter", 
            payload=f"{count} {size}",
            message_type="counter"
        )
    
    def publish_log(self, payload):
        self.safe_publish(
            topic=b"boards/esp32_b1/log",
            payload=f"{payload}",
            message_type="log"
        )


    def publish_status(self, status):
        self.safe_publish(
            topic=b"boards/esp32_b1/status", 
            payload=status, 
            retain=True,
            message_type="status"
        )
        
    def publish_last_state(self, state, total_production_count, total_time):
        self.safe_publish(
            topic=b"boards/esp32_b1/last_state", 
            payload=f"{state} {total_production_count} {total_time}", 
            retain=True,
            message_type="last_state"
        )

    def publish_temp(self, temp):
        self.safe_publish(
            topic=b"boards/esp32_b1/temp", 
            payload=temp,
            message_type="temp"
        )

    def publish_error(self, error):
        self.safe_publish(
            topic=b"boards/esp32_b1/error", 
            payload=error,
            message_type="error"
        )

    def publish_updateack(self, ack):
        self.safe_publish(
            topic=b"boards/esp32_b1/update_ack", 
            payload=ack,
            message_type="update_ack"
        )
    def publish_gate(self, gate_update):
        self.safe_publish(
            topic=b"boards/esp32_b1/gate_state",
            payload=gate_update,
            message_type="gate"
        )

    def get_queue_size(self):
        """Get current queue size for monitoring"""
        return len(self.message_queue)
    
    def clear_queue(self):
        """Clear all queued messages (use with caution)"""
        cleared_count = len(self.message_queue)
        self.message_queue.clear()
        print(f"Cleared {cleared_count} queued messages")

    
