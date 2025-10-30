import logging

logger = logging.getLogger(__name__)

def read_aws_config():
    config = {}
    try:
        with open("aws.properties") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or '=' not in line:
                    continue
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip()
    except FileNotFoundError:
        logger.warning("aws.properties not found")
    return config

