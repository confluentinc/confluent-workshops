import logging
import time
import pandas as pd
import boto3
from app.config.settings import aws_config

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for AWS Athena analytics operations"""
    
    def __init__(self):
        try:
            self.athena_client = boto3.client(
                'athena',
                region_name=aws_config.get('aws.region', 'us-east-1'),
                aws_access_key_id=aws_config.get('aws.access_key_id'),
                aws_secret_access_key=aws_config.get('aws.secret_access_key'),
                aws_session_token=aws_config.get('aws.session_token' , None)
            )
            self.athena_db = aws_config.get('athena.database')
            self.athena_table = aws_config.get('athena.table')
            self.qualified_table = f'"{self.athena_db}"."{self.athena_table}"'
        except Exception as e:
            logger.warning(f"AWS Athena client initialization failed: {e}")
            self.athena_client = None
    
    def execute_athena_query(self, query: str, database: str = "default") -> pd.DataFrame:
        """Execute Athena query and return results as DataFrame"""
        if not self.athena_client:
            logger.error("Athena client not initialized")
            return pd.DataFrame()
        
        try:
            logger.info(f"Executing Athena query: {query}")
            logger.info(f"Database: {database}")
            logger.info(f"Output location: {aws_config.get('athena.output_location')}")
            
            # Start query execution
            response = self.athena_client.start_query_execution(
                QueryString=query.replace('{self.qualified_table}', self.qualified_table),
                QueryExecutionContext={'Database': database},
                ResultConfiguration={
                    'OutputLocation': aws_config.get('athena.output_location', 's3://dspathenaworkshopqueries/')
                }
            )
            
            query_execution_id = response['QueryExecutionId']
            logger.info(f"Query execution ID: {query_execution_id}")
            
            # Wait for query to complete
            max_wait_time = 60  # Maximum wait time in seconds
            wait_time = 0
            
            while wait_time < max_wait_time:
                result = self.athena_client.get_query_execution(QueryExecutionId=query_execution_id)
                status = result['QueryExecution']['Status']['State']
                logger.info(f"Query status: {status}, waited {wait_time}s")
                
                if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    break
                time.sleep(2)
                wait_time += 2
            
            if status == 'SUCCEEDED':
                logger.info("Query succeeded, fetching results...")
                # Get query results
                results = self.athena_client.get_query_results(QueryExecutionId=query_execution_id)
                
                # Debug: Log the raw results structure
                logger.info(f"Results metadata: {results.get('ResultSet', {}).get('ResultSetMetadata', {})}")
                logger.info(f"Number of rows returned: {len(results.get('ResultSet', {}).get('Rows', []))}")
                
                # Convert to DataFrame
                if 'ResultSet' in results and 'Rows' in results['ResultSet']:
                    if len(results['ResultSet']['Rows']) > 0:
                        columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
                        logger.info(f"Columns: {columns}")
                        
                        rows = []
                        for i, row in enumerate(results['ResultSet']['Rows'][1:]):  # Skip header row
                            row_data = []
                            for field in row['Data']:
                                # Handle different data types
                                value = field.get('VarCharValue', field.get('BigIntValue', field.get('DoubleValue', '')))
                                row_data.append(value)
                            rows.append(row_data)
                            if i < 3:  # Log first 3 rows for debugging
                                logger.info(f"Row {i}: {row_data}")
                        
                        df = pd.DataFrame(rows, columns=columns)
                        logger.info(f"DataFrame created with shape: {df.shape}")
                        return df
                    else:
                        logger.warning("No data rows returned from query")
                        return pd.DataFrame()
                else:
                    logger.error("Invalid results structure")
                    return pd.DataFrame()
            elif status == 'FAILED':
                # Get failure reason
                failure_reason = result['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                logger.error(f"Query failed: {failure_reason}")
                return pd.DataFrame()
            else:
                logger.error(f"Query timed out or was cancelled. Final status: {status}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error executing Athena query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def get_click_trends_data(self) -> pd.DataFrame:
        """Get click trends data for analytics"""
        query = """
        SELECT 
            DATE_TRUNC('minute', CAST("$$timestamp" AS timestamp)) - 
            INTERVAL '1' MINUTE * (MINUTE(CAST("$$timestamp" AS timestamp)) % 5) as time_bucket,
            COUNT(*) as click_count
        FROM {self.qualified_table}
        WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
        GROUP BY 1
        ORDER BY time_bucket
        """
        return self.execute_athena_query(query)
    
    def get_product_type_distribution(self) -> pd.DataFrame:
        """Get product type distribution data"""
        query = """
        SELECT type as product_type, COUNT(*) as click_count
        FROM {self.qualified_table}
        WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
        GROUP BY type
        ORDER BY click_count DESC
        """
        return self.execute_athena_query(query)
    
    def get_total_clicks(self) -> int:
        """Get total clicks in last 24 hours"""
        query = """
        SELECT COUNT(*) as total_clicks
        FROM {self.qualified_table}
        WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
        """
        df = self.execute_athena_query(query)
        if not df.empty:
            return int(df['total_clicks'].iloc[0])
        return 0
    
    def get_top_users(self) -> pd.DataFrame:
        """Get top 5 active users"""
        query = """
        SELECT email, COUNT(*) as click_count
        FROM {self.qualified_table}
        WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
        GROUP BY email
        ORDER BY click_count DESC
        LIMIT 5
        """
        return self.execute_athena_query(query) 