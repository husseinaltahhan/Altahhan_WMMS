from supabase import create_client
from datetime import date

class Database:
    def __init__(self, url, key):
        self.client = create_client(url, key)

    def _today(self):
        return date.today().isoformat()

    # ------------------ Messages ------------------
    def id_insert_message(self, board_id, topic_id, payload):
        self.client.table("messages").insert({
            "publishing_board": board_id,
            "message_topic": topic_id,
            "payload": payload
        }).execute()

    def name_insert_message(self, board_name, topic_name, payload):
        b = self.client.table("esp32_boards").select("id").eq("esp_name", board_name).execute().data
        t = self.client.table("topics").select("id").eq("topic", topic_name).execute().data
        if not b or not t:
            raise ValueError("Board or topic not found")
        self.id_insert_message(b[0]["id"], t[0]["id"], payload)

    # ------------------ Production Log ------------------
    def update_cylinder_count(self, board_id, cylinder_count):
        self.client.table("production_log").upsert({
            "board_id": board_id,
            "log_date": self._today(),
            "cylinder_count": cylinder_count
        }, on_conflict="board_id,log_date").execute()

    def increment_production_count(self, board_id, cylinder_count, cylinder_size):
        today = self._today()
        # Ensure row exists
        self.client.table("production_log").upsert({
            "board_id": board_id,
            "log_date": today,
            "cylinder_count": 0
        }, on_conflict="board_id,log_date").execute()

        row = self.client.table("production_log").select("*").eq("board_id", board_id).eq("log_date", today).execute().data
        if not row:
            return
        row = row[0]
        updates = {
            "cylinder_count": (row.get("cylinder_count") or 0) + cylinder_count
        }
        if cylinder_size in row:
            updates[cylinder_size] = (row.get(cylinder_size) or 0) + cylinder_count

        self.client.table("production_log").update(updates).eq("board_id", board_id).eq("log_date", today).execute()

    def decrement_production_count(self, board_id):
        today = self._today()
        self.client.table("production_log").upsert({
            "board_id": board_id,
            "log_date": today,
            "cylinder_count": 0
        }, on_conflict="board_id,log_date").execute()

        row = self.client.table("production_log").select("cylinder_count").eq("board_id", board_id).eq("log_date", today).execute().data
        if row:
            new_val = max((row[0].get("cylinder_count") or 0) - 1, 0)
            self.client.table("production_log").update({"cylinder_count": new_val}).eq("board_id", board_id).eq("log_date", today).execute()

    def create_daily_log_entries(self):
        today = self._today()
        boards = {b["id"] for b in self.client.table("esp32_boards").select("id").execute().data}
        existing = {p["board_id"] for p in self.client.table("production_log").select("board_id").eq("log_date", today).execute().data}
        missing = boards - existing
        if missing:
            self.client.table("production_log").insert([{
                "board_id": bid,
                "log_date": today,
                "cylinder_count": 0
            } for bid in missing]).execute()

    def get_board_production_count(self, board_id):
        row = self.client.table("production_log").select("cylinder_count").eq("board_id", board_id).eq("log_date", self._today()).execute().data
        return row[0]["cylinder_count"] if row else 0

    # ------------------ Lookups ------------------
    def boardname_id_dict(self):
        rows = self.client.table("esp32_boards").select("esp_name,id").execute().data
        return {r["esp_name"]: r["id"] for r in rows}

    def topic_id_dict(self):
        rows = self.client.table("topics").select("topic,id").execute().data
        return {r["topic"]: r["id"] for r in rows}

    # ------------------ Board state ------------------
    def update_last_state(self, last_state, board_id):
        self.client.table("esp32_boards").update({"last_state": last_state}).eq("id", board_id).execute()

    def update_status(self, status, board_id):
        self.client.table("esp32_boards").update({"state": status}).eq("id", board_id).execute()

    def get_last_state(self, board_id):
        row = self.client.table("esp32_boards").select("last_state").eq("id", board_id).execute().data
        return row[0]["last_state"] if row else None

    # ------------------ Topics ------------------
    def insert_topic(self, topic_name):
        self.client.table("topics").upsert({"topic": topic_name}, on_conflict="topic").execute()
