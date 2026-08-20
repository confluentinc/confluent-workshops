"""
Avro schemas for F1 Leaderboard application
These schemas define the data contracts for Kafka messages
"""

# Driver Position Schema (Flat)
DRIVER_POSITION_SCHEMA = {
    "type": "record",
    "name": "DriverPosition",
    "namespace": "com.f1leaderboard",
    "fields": [
        {
            "name": "driver_name",
            "type": "string",
            "doc": "Name of the driver"
        },
        {
            "name": "position",
            "type": "int",
            "doc": "Current position in the race (1-10)"
        }
    ]
}


# Leaderboard Update Schema (for positions topic) - Flat
LEADERBOARD_UPDATE_SCHEMA = {
    "type": "record",
    "name": "LeaderboardUpdate",
    "namespace": "com.f1leaderboard",
    "fields": [
        {
            "name": "driver_name",
            "type": "string",
            "doc": "Name of the driver"
        },
        {
            "name": "position",
            "type": "int",
            "doc": "Current position in the race (1-10)"
        },
        {
            "name": "timestamp",
            "type": "long",
            "logicalType": "timestamp-millis",
            "doc": "Timestamp when the position was recorded"
        },
        {
            "name": "race_id",
            "type": ["null", "string"],
            "default": None,
            "doc": "Unique identifier for the race"
        },
        {
            "name": "team_name",
            "type": "string",
            "doc": "Team name of the driver"
        },
        {
            "name": "speed",
            "type": "double",
            "doc": "Current speed in km/h"
        }
    ]
}

# Driver Average Speed Key Schema (for upsert key) - matches Flink generated schema
DRIVER_AVG_SPEED_KEY_SCHEMA = {
    "type": "record",
    "name": "driver_avg_speed_key",
    "namespace": "org.apache.flink.avro.generated.record",
    "fields": [
        {
            "name": "driver_name",
            "type": "string"
        },
        {
            "name": "race_id",
            "type": "string"
        }
    ]
}

# Driver Average Speed Value Schema (for upsert value) - JSON Schema format
DRIVER_AVG_SPEED_VALUE_SCHEMA = {
    "additionalProperties": False,
    "properties": {
        "avg_speed": {
            "connect.index": 0,
            "oneOf": [
                {
                    "type": "null"
                },
                {
                    "connect.type": "float64",
                    "type": "number"
                }
            ]
        }
    },
    "title": "Record",
    "type": "object"
}

# Schema Registry subject names
SCHEMA_SUBJECTS = {
    "positions": "f1-driver-positions2-value",
    "driver_avg_speed_key": "driver-avg-speed-key",
    "driver_avg_speed_value": "driver-avg-speed-value"
}
