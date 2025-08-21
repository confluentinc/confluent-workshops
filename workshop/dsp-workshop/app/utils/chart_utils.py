import pandas as pd
import logging

logger = logging.getLogger(__name__)

def create_click_trends_chart(click_trends_df: pd.DataFrame) -> dict:
    """Create click trends line chart data"""
    if click_trends_df.empty:
        return {}
    
    try:
        click_trends_df['click_count'] = pd.to_numeric(click_trends_df['click_count'], errors='coerce')
        
        # Convert timestamps to string format for better display
        time_labels = [str(ts) for ts in click_trends_df['time_bucket']]
        click_values = click_trends_df['click_count'].tolist()
        
        return {
            'data': [{
                'type': 'scatter',
                'mode': 'lines+markers',
                'x': time_labels,
                'y': click_values,
                'line': {'color': '#667eea', 'width': 3},
                'marker': {'size': 6, 'color': '#667eea'},
                'hovertemplate': '<b>Time:</b> %{x}<br><b>Clicks:</b> %{y}<extra></extra>'
            }],
            'layout': {
                'title': 'Product Click Trends (5-Minute Intervals - Last 24 Hours)',
                'height': 400,
                'xaxis': {'title': 'Time', 'tickangle': -45},
                'yaxis': {'title': 'Clicks'}
            }
        }
    except Exception as e:
        logger.error(f"Error creating click trends chart: {e}")
        return {}

def create_product_type_chart(product_type_df: pd.DataFrame) -> dict:
    """Create product type distribution pie chart data"""
    if product_type_df.empty:
        return {}
    
    try:
        # Ensure proper data types and clean data
        product_type_df['click_count'] = pd.to_numeric(product_type_df['click_count'], errors='coerce')
        product_type_df = product_type_df.dropna()  # Remove any NaN values
        
        # Debug logging
        logger.info(f"Product type data: {product_type_df.to_dict('records')}")
        
        labels = product_type_df['product_type'].tolist()
        values = product_type_df['click_count'].tolist()
        
        return {
            'data': [{
                'type': 'pie',
                'labels': labels,
                'values': values,
                'hovertemplate': '<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                'textinfo': 'percent+label',
                'textposition': 'inside'
            }],
            'layout': {
                'title': 'Product Type Distribution (Last 24 Hours)',
                'height': 400
            }
        }
    except Exception as e:
        logger.error(f"Error creating product type chart: {e}")
        return {}

def create_top_users_chart(top_users_df: pd.DataFrame) -> dict:
    """Create top users bar chart data"""
    if top_users_df.empty:
        return {}
    
    try:
        top_users_df['click_count'] = pd.to_numeric(top_users_df['click_count'], errors='coerce')
        
        user_emails = top_users_df['email'].tolist()
        user_clicks = top_users_df['click_count'].tolist()
        
        return {
            'data': [{
                'type': 'bar',
                'orientation': 'h',
                'x': user_clicks,
                'y': user_emails,
                'marker': {'color': '#764ba2'},
                'hovertemplate': '<b>User:</b> %{y}<br><b>Clicks:</b> %{x}<extra></extra>'
            }],
            'layout': {
                'title': 'Top 5 Active Users (Last 24 Hours)',
                'height': 400,
                'xaxis': {'title': 'Clicks'},
                'yaxis': {'title': 'User Email'},
                'margin': {'l': 200}  # Add left margin for long email addresses
            }
        }
    except Exception as e:
        logger.error(f"Error creating top users chart: {e}")
        return {} 