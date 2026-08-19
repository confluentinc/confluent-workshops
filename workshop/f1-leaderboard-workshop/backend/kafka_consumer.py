import json
import threading
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
from config import config
from models import DriverPosition, LeaderboardUpdate
from schemas import LEADERBOARD_UPDATE_SCHEMA, DRIVER_AVG_SPEED_KEY_SCHEMA, DRIVER_AVG_SPEED_VALUE_SCHEMA, SCHEMA_SUBJECTS

class KafkaConsumer:
    def __init__(self):
        kafka_config = config.get_kafka_config()
        kafka_config['group.id'] = config.get_consumer_group()
        kafka_config['auto.offset.reset'] = 'earliest'
        # Ultra-aggressive consumer config for maximum real-time performance
        kafka_config['fetch.min.bytes'] = 1  # Fetch messages as soon as available
        kafka_config['fetch.wait.max.ms'] = 0  # No wait on server - immediate fetch
        kafka_config['max.partition.fetch.bytes'] = 1048576  # 1MB per partition
        kafka_config['enable.auto.commit'] = True  # Auto-commit for speed
        kafka_config['queued.max.messages.kbytes'] = 51200  # 50MB queue for high throughput
        kafka_config['session.timeout.ms'] = 30000  # 30 second session timeout
        kafka_config['heartbeat.interval.ms'] = 10000  # 10 second heartbeat
        
        self.consumer = Consumer(kafka_config)
        self.topics = list(config.get_topic_names().values())
        
        # Setup Schema Registry
        schema_registry_config = config.get_schema_registry_config()
        self.schema_registry_client = SchemaRegistryClient(schema_registry_config)
        
        # Setup deserializers
        self.positions_deserializer = AvroDeserializer(
            self.schema_registry_client,
            json.dumps(LEADERBOARD_UPDATE_SCHEMA),
            from_dict=self._positions_from_dict
        )
        
        # Setup deserializers for avg speed (key-value structure) - use schema lookup for low latency
        try:
            # Get the subject names for avg speed topic
            avg_speed_topic = config.get_topic_names()['driver_avg_speed']
            key_subject_name = f"{avg_speed_topic}-key"
            value_subject_name = f"{avg_speed_topic}-value"
            
            # Look up existing schemas instead of using local schemas
            key_schema = self.schema_registry_client.get_latest_version(key_subject_name)
            value_schema = self.schema_registry_client.get_latest_version(value_subject_name)
            
            
            self.avg_speed_key_deserializer = AvroDeserializer(
                self.schema_registry_client,
                key_schema.schema.schema_str,
                from_dict=self._avg_speed_key_from_dict
            )
            
            self.avg_speed_value_deserializer = JSONDeserializer(
                value_schema.schema.schema_str,
                from_dict=self._avg_speed_value_from_dict
            )
        except Exception as e:
            # Fallback to local schemas if lookup fails
            self.avg_speed_key_deserializer = AvroDeserializer(
                self.schema_registry_client,
                json.dumps(DRIVER_AVG_SPEED_KEY_SCHEMA),
                from_dict=self._avg_speed_key_from_dict
            )
            
            self.avg_speed_value_deserializer = JSONDeserializer(
                json.dumps(DRIVER_AVG_SPEED_VALUE_SCHEMA),
                from_dict=self._avg_speed_value_from_dict
            )
        
        
        # In-memory storage for latest data
        self.latest_positions = []  # Legacy - for backward compatibility
        self.race_positions = {}  # New - grouped by race_id
        self.race_avg_speeds = {}  # New - grouped by race_id
        self.position_callbacks = []
        self.avg_speed_callbacks = []
        
        # Thread safety locks for concurrent access
        self.positions_lock = threading.Lock()
        self.avg_speeds_lock = threading.Lock()
        
        self.running = False
        self.consumer_thread = None
    
    def _positions_from_dict(self, obj, ctx):
        """Convert dictionary to DriverPosition object"""
        if obj is None:
            return None
        
        return {
            'driver_name': obj['driver_name'],
            'position': obj['position'],
            'timestamp': datetime.fromtimestamp(obj['timestamp'] / 1000).isoformat(),  # Convert from milliseconds to ISO string
            'race_id': obj.get('race_id'),  # Include race_id if present
            'team_name': obj.get('team_name'),
            'speed': obj.get('speed')
        }
    
    def _avg_speed_key_from_dict(self, obj, ctx):
        """Convert dictionary to DriverAverageSpeedKey object"""
        if obj is None:
            return None
        
        return {
            'driver_name': obj['driver_name'],
            'race_id': obj['race_id']
        }
    
    def _avg_speed_value_from_dict(self, obj, ctx):
        """Convert dictionary to DriverAverageSpeedValue object"""
        if obj is None:
            return None
        
        # Handle the JSON Schema format where avg_speed can be null
        avg_speed = obj.get('avg_speed')
        if avg_speed is None:
            return None
            
        return {
            'avg_speed': float(avg_speed) if avg_speed is not None else 0.0
        }
    
    
    def add_position_callback(self, callback):
        """Add callback for position updates"""
        self.position_callbacks.append(callback)
    
    def add_avg_speed_callback(self, callback):
        """Add callback for average speed updates"""
        self.avg_speed_callbacks.append(callback)
    
    
    def start_consuming(self):
        """Start consuming from Kafka topics"""
        if self.running:
            return
        
        self.running = True
        self.consumer_thread = threading.Thread(target=self._consume_loop)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        print(f"Started consuming from topics: {self.topics}")
    
    def stop_consuming(self):
        """Stop consuming from Kafka topics"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join()
        self.consumer.close()
        print("Stopped consuming from Kafka")
    
    def _consume_loop(self):
        """Ultra-fast continuous consumption loop for millisecond-level updates"""
        self.consumer.subscribe(self.topics)
        print(f"Consumer subscribed to topics: {self.topics}")
        
        # Track driver_avg_speed topic for optimized processing (cache to avoid repeated lookups)
        avg_speed_topic = config.get_topic_names()['driver_avg_speed']
        positions_topic = config.get_topic_names()['positions']
        
        # Pre-create serialization contexts to avoid repeated object creation
        avg_speed_key_ctx = SerializationContext(avg_speed_topic, MessageField.KEY)
        avg_speed_value_ctx = SerializationContext(avg_speed_topic, MessageField.VALUE)
        positions_value_ctx = SerializationContext(positions_topic, MessageField.VALUE)
        
        while self.running:
            try:
                # Ultra-aggressive polling - zero timeout for maximum real-time performance
                msg_pack = self.consumer.consume(num_messages=1000, timeout=0.0)
                
                if not msg_pack:
                    # No messages available, continue immediately for next poll
                    continue
                
                # Process all messages in batch for maximum throughput
                for msg in msg_pack:
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        else:
                            print(f"Consumer error: {msg.error()}")
                            continue
                    
                    # Parse message using appropriate deserializer
                    topic = msg.topic()
                    
                    if topic == positions_topic:
                        # Deserialize positions using Avro
                        try:
                            data = self.positions_deserializer(
                                msg.value(),
                                positions_value_ctx
                            )
                            if data:
                                self._handle_position_update(data)
                        except Exception as e:
                            print(f"Error deserializing position message: {e}")
                            continue
                            
                    elif topic == avg_speed_topic:
                        # Priority processing for driver_avg_speed - process immediately
                        try:
                            # Deserialize key and value
                            key_data = self.avg_speed_key_deserializer(
                                msg.key(),
                                avg_speed_key_ctx
                            )
                            value_data = self.avg_speed_value_deserializer(
                                msg.value(),
                                avg_speed_value_ctx
                            )
                            
                            if key_data is None or value_data is None:
                                continue
                            
                            # Process immediately without any delays
                            self._handle_avg_speed_update(key_data, value_data)
                            
                        except Exception as e:
                            print(f"Error deserializing driver_avg_speed message: {e}")
                            continue
                
            except Exception as e:
                print(f"Error in consume loop: {e}")
                continue
    
    def _handle_position_update(self, data):
        """Handle driver position updates - thread-safe"""
        try:
            # Update the position for this specific driver
            driver_name = data['driver_name']
            position = data['position']
            race_id = data.get('race_id')
            
            # Handle race-based positions
            if race_id:
                with self.positions_lock:
                    if race_id not in self.race_positions:
                        self.race_positions[race_id] = []
                    
                    # Find and update existing position or add new one for this race
                    updated = False
                    for i, pos in enumerate(self.race_positions[race_id]):
                        if pos['driver_name'] == driver_name:
                            self.race_positions[race_id][i] = data
                            updated = True
                            break
                    
                    if not updated:
                        self.race_positions[race_id].append(data)
                    
                    # Keep only the latest 10 positions per race (one per driver)
                    if len(self.race_positions[race_id]) > 10:
                        self.race_positions[race_id] = self.race_positions[race_id][-10:]
                    
                    positions_copy = self.race_positions[race_id].copy()
                
                # Notify callbacks with race context (outside lock)
                for callback in self.position_callbacks:
                    try:
                        callback(positions_copy, race_id)
                    except Exception as e:
                        print(f"Error in position callback: {e}")
                
            else:
                # Legacy handling for positions without race_id
                with self.positions_lock:
                    # Find and update existing position or add new one
                    updated = False
                    for i, pos in enumerate(self.latest_positions):
                        if pos['driver_name'] == driver_name:
                            self.latest_positions[i] = data
                            updated = True
                            break
                    
                    if not updated:
                        self.latest_positions.append(data)
                    
                    # Keep only the latest 10 positions (one per driver)
                    if len(self.latest_positions) > 10:
                        self.latest_positions = self.latest_positions[-10:]
                    
                    positions_copy = self.latest_positions.copy()
                
                # Notify callbacks (outside lock)
                for callback in self.position_callbacks:
                    try:
                        callback(positions_copy)
                    except Exception as e:
                        print(f"Error in position callback: {e}")
                
            
        except Exception as e:
            print(f"Error handling position update: {e}")
    
    def _handle_avg_speed_update(self, key_data, value_data):
        """Handle driver average speed updates with thread-safe upsert for millisecond-level updates"""
        try:
            if not key_data or not value_data:
                return
                
            driver_name = key_data.get('driver_name')
            race_id = key_data.get('race_id')
            avg_speed = value_data.get('avg_speed')
            
            if not driver_name or not race_id or avg_speed is None:
                return
            
            # Quick team name lookup (minimal lock time)
            team_name = 'Unknown Team'
            with self.positions_lock:
                if race_id in self.race_positions:
                    for pos in self.race_positions[race_id]:
                        if pos.get('driver_name') == driver_name and pos.get('team_name'):
                            team_name = pos['team_name']
                            break
            
            # Create data structure outside lock
            combined_data = {
                'driver_name': driver_name,
                'race_id': race_id,
                'average_speed': float(avg_speed),
                'timestamp': datetime.now().isoformat(),
                'team_name': team_name
            }
            
            # Thread-safe fast upsert with minimal lock time
            with self.avg_speeds_lock:
                if race_id not in self.race_avg_speeds:
                    self.race_avg_speeds[race_id] = {}
                # Fast upsert - update immediately
                self.race_avg_speeds[race_id][driver_name] = combined_data
            
            # Notify callbacks outside lock to avoid blocking
            for callback in self.avg_speed_callbacks:
                try:
                    callback(combined_data, race_id)
                except Exception as e:
                    print(f"Error in avg speed callback: {e}")
            
        except Exception as e:
            print(f"Error handling avg speed update: {e}")
    
    
    def get_latest_positions(self, race_id=None):
        """Get latest driver positions - thread-safe"""
        with self.positions_lock:
            if race_id:
                return self.race_positions.get(race_id, []).copy()
            return self.latest_positions.copy()
    
    def get_race_avg_speeds(self, race_id):
        """Get average speeds for a specific race - thread-safe and optimized for millisecond access"""
        with self.avg_speeds_lock:
            if race_id not in self.race_avg_speeds:
                return []
            
            # Fast copy and sort - minimal operations
            avg_speeds = list(self.race_avg_speeds[race_id].values())
        
        # Sort outside lock to minimize lock time
        avg_speeds.sort(key=lambda x: x.get('average_speed', 0), reverse=True)
        return avg_speeds
    

# Global consumer instance
kafka_consumer = KafkaConsumer()
