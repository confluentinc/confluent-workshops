import boto3
import logging
from config.aws_config import read_aws_config

logger = logging.getLogger(__name__)

aws_config = read_aws_config()

try:
    athena_client = boto3.client(
        'athena',
        region_name=aws_config.get('aws.region', 'us-east-1'),
        aws_access_key_id=aws_config.get('aws.access_key_id'),
        aws_secret_access_key=aws_config.get('aws.secret_access_key'),
        aws_session_token=aws_config.get('aws.session_token')
    )
except Exception as e:
    logger.warning(f"Athena init failed: {e}")
    athena_client = None

athena_db = aws_config.get("athena.database", "default")
athena_output = aws_config.get("athena.output_location")
