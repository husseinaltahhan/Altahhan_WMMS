class BoardPublisher():
    def __init__(self, client):
        self.client = client

    def publish_counter(self, count):
        self.client.publish(b"boards/esp32_b1/update_counter", count)

    def publish_status(self, status):
        self.client.publish(b"boards/esp32_b1/status", status, retain=True)
        
    def publish_last_state(self, state, total_production_count, current_cylinder):
        self.client.publish(b"boards/esp32_b1/last_state", f"{state} {total_production_count} {current_cylinder}", retain=True)

    def publish_temp(self, temp):
        self.client.publish(b"boards/esp32_b1/temp", temp)

    def publish_error(self, error):
        self.client.publish(b"boards/esp32_b1/error", error)

    def publish_updateack(self, ack):
        self.client.publish(b"boards/esp32_b1/update_ack", ack)

