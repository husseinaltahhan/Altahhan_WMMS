import os
from typing import Dict, Any

class Config:
    """Configuration class for WMMS application"""
    
    def __init__(self):
        self.db_config = {
            'dbname': os.getenv('DB_NAME', 'MQTT_System'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'altahhan2004!'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
        
        self.mqtt_config = {
            'host': os.getenv('MQTT_HOST', 'localhost'),
            'port': int(os.getenv('MQTT_PORT', '1883')),
            'keepalive': int(os.getenv('MQTT_KEEPALIVE', '60'))
        }
        
        self.flask_config = {
            'host': os.getenv('FLASK_HOST', '0.0.0.0'),
            'port': int(os.getenv('FLASK_PORT', '80')),
            'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        }
    
    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.db_config.copy()
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """Get MQTT configuration"""
        return self.mqtt_config.copy()
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask configuration"""
        return self.flask_config.copy()

# Global config instance
config = Config()