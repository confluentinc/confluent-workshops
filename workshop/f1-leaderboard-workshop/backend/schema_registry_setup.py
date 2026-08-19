"""
Script to register schemas with Confluent Schema Registry
Run this script to register the schemas before starting the application
"""

import json
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from config import config
from schemas import LEADERBOARD_UPDATE_SCHEMA, COMMENTARY_SCHEMA, SCHEMA_SUBJECTS

def register_schemas():
    """Register schemas with Confluent Schema Registry"""
    schema_registry_config = config.get_schema_registry_config()
    client = SchemaRegistryClient(schema_registry_config)
    
    try:
        # Register LeaderboardUpdate schema
        positions_subject = SCHEMA_SUBJECTS['positions']
        positions_schema_str = json.dumps(LEADERBOARD_UPDATE_SCHEMA)
        
        print(f"Registering schema for subject: {positions_subject}")
        schema = Schema(positions_schema_str, schema_type="AVRO")
        schema_id = client.register_schema(
            subject_name=positions_subject,
            schema=schema
        )
        print(f"✅ Successfully registered positions schema with ID: {schema_id}")
        
        # Register Commentary schema
        commentary_subject = SCHEMA_SUBJECTS['commentary']
        commentary_schema_str = json.dumps(COMMENTARY_SCHEMA)
        
        print(f"Registering schema for subject: {commentary_subject}")
        schema = Schema(commentary_schema_str, schema_type="AVRO")
        schema_id = client.register_schema(
            subject_name=commentary_subject,
            schema=schema
        )
        print(f"✅ Successfully registered commentary schema with ID: {schema_id}")
        
        print("\n🎉 All schemas registered successfully!")
        print("You can now start the application with: python main.py")
        
    except Exception as e:
        print(f"❌ Error registering schemas: {e}")
        print("\nMake sure your Schema Registry credentials are correct in config.yaml")
        print("and that the Schema Registry is accessible.")

if __name__ == "__main__":
    register_schemas()
