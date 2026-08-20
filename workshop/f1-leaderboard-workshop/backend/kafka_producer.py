import asyncio
import json
import random
from datetime import datetime
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
from config import config
from models import DriverPosition, F1_DRIVERS
from schemas import LEADERBOARD_UPDATE_SCHEMA, SCHEMA_SUBJECTS

class PositionProducer:
    def __init__(self):
        kafka_config = config.get_kafka_config()
        self.producer = Producer(kafka_config)
        self.topic = config.get_topic_names()['positions']
        self.drivers = F1_DRIVERS
        self.running = False
        
        # Setup Schema Registry
        schema_registry_config = config.get_schema_registry_config()
        self.schema_registry_client = SchemaRegistryClient(schema_registry_config)
        
        # Setup Avro serializer for positions
        self.avro_serializer = AvroSerializer(
            self.schema_registry_client,
            json.dumps(LEADERBOARD_UPDATE_SCHEMA),
            to_dict=self._leaderboard_update_to_dict
        )
    
    def _leaderboard_update_to_dict(self, obj, ctx):
        """Convert LeaderboardUpdate object to dictionary for JSON serialization"""
        if obj is None:
            return None
        
        return {
            "driver_name": obj['driver_name'],
            "position": obj['position'],
            "timestamp": int(obj['timestamp'].timestamp() * 1000),  # Convert to milliseconds
            "race_id": obj.get('race_id'),  # Include race_id if present
            "team_name": obj.get('team_name'),
            "speed": obj.get('speed')
        }
    
    def delivery_callback(self, err, msg):
        if err:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')
    
    def generate_random_positions(self):
        """Generate random positions for all 10 drivers"""
        positions = list(range(1, 11))  # 1 to 10
        random.shuffle(positions)
        
        driver_positions = []
        for i, driver in enumerate(self.drivers):
            position = DriverPosition(
                driver_name=driver.name,
                position=positions[i]
            )
            driver_positions.append(position)
        
        return driver_positions
    
    async def produce_race_positions(self, race_id: str, positions: list):
        """Produce driver positions for a specific race"""
        try:
            # Send individual position updates
            for pos in positions:
                # Create leaderboard update data for each driver
                update_data = {
                    "driver_name": pos['driver_name'],
                    "position": pos['position'],
                    "timestamp": pos['timestamp'],
                    "race_id": race_id,
                    "team_name": pos['team_name'],
                    "speed": pos['speed']
                }
                
                # Serialize using Avro
                serialized_data = self.avro_serializer(
                    update_data,
                    SerializationContext(self.topic, MessageField.VALUE)
                )
                
                # Produce to Kafka with race_id as key
                self.producer.produce(
                    self.topic,
                    key=race_id,  # Use race_id as the message key
                    value=serialized_data,
                    callback=self.delivery_callback
                )
            
            # Flush to ensure messages are sent
            self.producer.flush()
            
            position_summary = [f"{pos['driver_name']}: P{pos['position']}" for pos in positions]
            
        except Exception as e:
            print(f"Error producing race positions for {race_id}: {e}")

    async def produce_positions(self):
        """Legacy method - kept for backward compatibility but not used in race mode"""
        self.running = True
        print("Starting position producer...")
        
        while self.running:
            try:
                positions = self.generate_random_positions()
                
                # Send individual position updates
                for pos in positions:
                    # Create leaderboard update data for each driver
                    update_data = {
                        "driver_name": pos.driver_name,
                        "position": pos.position,
                        "timestamp": datetime.now()
                    }
                    
                    # Serialize using JSON_SR
                    serialized_data = self.avro_serializer(
                        update_data,
                        SerializationContext(self.topic, MessageField.VALUE)
                    )
                    
                    # Produce to Kafka
                    self.producer.produce(
                        self.topic,
                        value=serialized_data,
                        callback=self.delivery_callback
                    )
                
                # Flush to ensure messages are sent
                self.producer.flush()
                
                print(f"Produced positions update: {[f'{pos.driver_name}: P{pos.position}' for pos in positions]}")
                
                # Wait 1 second
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error producing positions: {e}")
                await asyncio.sleep(1)
    
    def stop(self):
        """Stop the producer"""
        self.running = False
        self.producer.flush()

# Global producer instance
position_producer = PositionProducer()
