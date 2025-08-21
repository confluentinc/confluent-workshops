import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the base directory (dsp-workshop)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ConfigManager:
    """Manages configuration loading from property files"""
    
    @staticmethod
    def read_property_file(file_path: str) -> Dict[str, str]:
        """Read configuration from a property file"""
        config = {}
        try:
            with open(file_path) as fh:
                for line in fh:
                    line = line.strip()
                    if len(line) != 0 and line[0] != "#":
                        parameter, value = line.strip().split('=', 1)
                        config[parameter] = value.strip()
        except FileNotFoundError:
            logger.warning(f"{file_path} file not found")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        return config
    
    @staticmethod
    def get_psql_config() -> Dict[str, str]:
        """Get PostgreSQL configuration"""
        return ConfigManager.read_property_file(os.path.join(BASE_DIR, "psqlclient.properties"))
    
    @staticmethod
    def get_kafka_config() -> Dict[str, str]:
        """Get Kafka configuration"""
        full_config = ConfigManager.read_property_file(os.path.join(BASE_DIR, "client.properties"))
        kafka_keys = {
            "bootstrap.servers",
            "security.protocol",
            "sasl.mechanisms",
            "sasl.username",
            "sasl.password"
        }
        return {k: v for k, v in full_config.items() if k in kafka_keys}
    
    @staticmethod
    def get_aws_config() -> Dict[str, str]:
        """Get AWS configuration"""
        config = ConfigManager.read_property_file(os.path.join(BASE_DIR, "aws.properties"))
        if not config:
            logger.warning("aws.properties file not found, using default AWS config")
            config = {
                'aws.region': 'us-east-1',
                'athena.output_location': 's3://dspathenaworkshopqueries/'
            }
        return config

# Global configuration instances
psql_config = ConfigManager.get_psql_config()
kafka_config = ConfigManager.get_kafka_config()
aws_config = ConfigManager.get_aws_config() 