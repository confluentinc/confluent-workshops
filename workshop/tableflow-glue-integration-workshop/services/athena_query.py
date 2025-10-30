import logging, time
import pandas as pd
from .athena_client import athena_client, athena_db, athena_output

logger = logging.getLogger(__name__)

def execute_athena_query(query: str, database: str = athena_db):
    if not athena_client:
        logger.error("Athena client not initialized")
        return pd.DataFrame()
    try:
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': athena_output}
        )
        qid = response['QueryExecutionId']

        wait_time = 0
        status = "RUNNING"
        while wait_time < 60:
            result = athena_client.get_query_execution(QueryExecutionId=qid)
            status = result['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(2)
            wait_time += 2

        if status != 'SUCCEEDED':
            logger.error(f"Query failed or timed out. Status: {status}")
            return pd.DataFrame()

        results = athena_client.get_query_results(QueryExecutionId=qid)
        if 'ResultSet' not in results or 'Rows' not in results['ResultSet']:
            return pd.DataFrame()

        columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        rows = []
        for row in results['ResultSet']['Rows'][1:]:
            rows.append([field.get('VarCharValue', '') for field in row['Data']])
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return pd.DataFrame()