import json
import random
import logging
from typing import List, Dict, Any
from collections import OrderedDict
from confluent_kafka import Producer, Consumer
from app.config.settings import kafka_config
import threading

logger = logging.getLogger(__name__)

class KafkaService:
    """Service for Kafka operations"""
    
    def __init__(self):
        self.producer = Producer(kafka_config)
        self.trending_consumer = None
        self.suggestions_consumer = None
        self.trending_thread = None
        self.suggestions_thread = None
        self.running = False
    
    def produce_message(self, topic: str, message: Dict[str, Any]):
        """Produce a message to Kafka topic"""
        try:
            message_str = json.dumps(message).encode("utf-8")
            self.producer.produce(topic, value=message_str)
            self.producer.flush()
            logger.info(f"Message produced to topic {topic}")
        except Exception as e:
            logger.error(f"Error producing message to {topic}: {e}")
    
    def start_consumer(self, trending_topic, suggestions_topic, db_update_callback):
        logger.info(f"Starting consumers for trending: {trending_topic}, suggestions: {suggestions_topic}")
        
        if (self.trending_thread and self.trending_thread.is_alive()) or (self.suggestions_thread and self.suggestions_thread.is_alive()):
            logger.info("Consumers already running, skipping startup")
            return  # Already running
        
        self.running = True
        logger.info("Setting running flag to True")
        
        # Start trending consumer thread
        logger.info("Creating trending consumer thread...")
        self.trending_thread = threading.Thread(
            target=self._consume_trending_loop,
            args=(trending_topic, db_update_callback),
            daemon=True
        )
        self.trending_thread.start()
        logger.info(f"Trending consumer thread started: {self.trending_thread.ident}")
        
        # Start suggestions consumer thread
        logger.info("Creating suggestions consumer thread...")
        self.suggestions_thread = threading.Thread(
            target=self._consume_suggestions_loop,
            args=(suggestions_topic, db_update_callback),
            daemon=True
        )
        self.suggestions_thread.start()
        logger.info(f"Suggestions consumer thread started: {self.suggestions_thread.ident}")
        
        logger.info(f"Started separate consumers for trending topic: {trending_topic} and suggestions topic: {suggestions_topic}")
        logger.info(f"Trending thread alive: {self.trending_thread.is_alive()}, Suggestions thread alive: {self.suggestions_thread.is_alive()}")

    def stop_consumer(self):
        self.running = False
        if self.trending_consumer:
            self.trending_consumer.close()
        if self.suggestions_consumer:
            self.suggestions_consumer.close()

    def _consume_trending_loop(self, trending_topic, db_update_callback):
        """Consumer loop specifically for trending products topic"""
        logger.info(f"=== TRENDING CONSUMER LOOP STARTED for topic: {trending_topic} ===")
        from confluent_kafka import Consumer
        consumer_config = kafka_config.copy()
        consumer_config["group.id"] = "dsp-trending-consumer01"
        consumer_config["auto.offset.reset"] = "latest"
        consumer_config["enable.auto.commit"] = False
        
        self.trending_consumer = Consumer(consumer_config)
        self.trending_consumer.subscribe([trending_topic])
        logger.info(f"Started trending consumer for topic: {trending_topic}")
        
        try:
            while self.running:
                msg = self.trending_consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error(f"Trending consumer error: {msg.error()}")
                    continue
                
                topic = msg.topic()
                key = msg.key()
                value = msg.value()
                
                logger.info(f"Received trending message from topic {topic}: key={key}, value={value}")
                
                if not value:
                    logger.warning(f"No value in trending message from topic {topic}")
                    continue
                
                try:
                    # Handle different message formats
                    key_data = json.loads(key[5:].decode("utf-8"))
                    value_data = json.loads(value[5:].decode("utf-8"))
                    
                    logger.info(f"Processed trendings message - Topic: {topic}, Key: {key_data}, Value: {value_data}")
                    db_update_callback(topic, key_data, value_data)
                    self.trending_consumer.commit(message=msg)
                    
                except Exception as e:
                    logger.error(f"Error processing trending message: {e}")
                    logger.error(f"Raw trending message - Topic: {topic}, Key: {key}, Value: {value}")
        except Exception as e:
            logger.error(f"Trending consumption failed: {e}")
        finally:
            if self.trending_consumer:
                self.trending_consumer.close()
            logger.info("=== TRENDING CONSUMER LOOP ENDED ===")

    def _consume_suggestions_loop(self, suggestions_topic, db_update_callback):
        """Consumer loop specifically for personalized suggestions topic"""
        logger.info(f"=== SUGGESTIONS CONSUMER LOOP STARTED for topic: {suggestions_topic} ===")
        from confluent_kafka import Consumer
        consumer_config = kafka_config.copy()
        consumer_config["group.id"] = "dsp-suggestions-consumer2"
        consumer_config["auto.offset.reset"] = "earliest"
        consumer_config["enable.auto.commit"] = False
        
        self.suggestions_consumer = Consumer(consumer_config)
        self.suggestions_consumer.subscribe([suggestions_topic])
        logger.info(f"Started suggestions consumer for topic: {suggestions_topic}")
        
        try:
            while self.running:
                msg = self.suggestions_consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error(f"Suggestions consumer error: {msg.error()}")
                    continue
                
                topic = msg.topic()
                key = msg.key()
                value = msg.value()
                
                logger.info(f"Received suggestions message from topic {topic}: key={key}, value={value}")
                
                if not value:
                    logger.warning(f"No value in suggestions message from topic {topic}")
                    continue
                
                try:
                    # Handle different message formats
                    key_data = json.loads(key[5:].decode("utf-8"))
                    value_data = json.loads(value[5:].decode("utf-8"))
                    
                    logger.info(f"Processed suggestions message - Topic: {topic}, Key: {key_data}, Value: {value_data}")
                    
                    db_update_callback(topic, key_data, value_data)
                    self.suggestions_consumer.commit(message=msg)
                    
                except Exception as e:
                    logger.error(f"Error processing suggestions message: {e}")
                    logger.error(f"Raw suggestions message - Topic: {topic}, Key: {key}, Value: {value}")
        except Exception as e:
            logger.error(f"Suggestions consumption failed: {e}")
        finally:
            if self.suggestions_consumer:
                self.suggestions_consumer.close()
            logger.info("=== SUGGESTIONS CONSUMER LOOP ENDED ===")

# Import here to avoid circular imports
from app.models.models import Product 