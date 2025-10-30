import logging
import pandas as pd
from .athena_query import execute_athena_query

logger = logging.getLogger(__name__)

def load_charts():
    charts = {}
    try:
        # --- Top Customer Locations ---
        df = execute_athena_query("""
            SELECT customer_location,
                   SUM(total_order_value) AS total_sales
            FROM ecommerce_orders
            GROUP BY customer_location
            ORDER BY total_sales DESC
            LIMIT 18;
        """)
        if not df.empty:
            df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')
            charts['top_customers'] = {
                'data': [{
                    'type': 'bar',
                    'x': df['customer_location'].tolist(),
                    'y': df['total_sales'].tolist(),
                    'marker': {'color': '#2ca02c'}
                }],
                'layout': {
                    'title': 'Top Customer Locations by Sales',
                    'xaxis': {'title': 'Customer Location'},
                    'yaxis': {'title': 'Total Sales'}
                }
            }

        # --- Top Categories by Profit ---
        df = execute_athena_query("""
            SELECT category, SUM(profit_margin) AS total_profit
            FROM ecommerce_orders
            GROUP BY category
            ORDER BY total_profit DESC
            LIMIT 5;
        """)
        if not df.empty:
            df['total_profit'] = pd.to_numeric(df['total_profit'], errors='coerce')
            charts['top_categories'] = {
                'data': [{
                    'type': 'pie',
                    'labels': df['category'].tolist(),
                    'values': df['total_profit'].tolist()
                }],
                'layout': {'title': 'Top Product Categories by Profit'}
            }

        # --- Weekly Sales for Last 7 Weeks ---
        df = execute_athena_query("""
            SELECT 
                date_trunc('week', DATE_PARSE(order_date, '%Y-%m-%dT%H:%i:%s.%f')) AS week_start,
                SUM(total_order_value) AS weekly_sales
            FROM ecommerce_orders
            WHERE DATE_PARSE(order_date, '%Y-%m-%dT%H:%i:%s.%f') >= date_add('week', -7, current_date)
            GROUP BY date_trunc('week', DATE_PARSE(order_date, '%Y-%m-%dT%H:%i:%s.%f'))
            ORDER BY week_start ASC;
        """)
        if not df.empty:
            df['weekly_sales'] = pd.to_numeric(df['weekly_sales'], errors='coerce')
            df['week_start'] = pd.to_datetime(df['week_start'], errors='coerce')
            charts['weekly_sales'] = {
                'data': [{
                    'type': 'bar',
                    'x': df['week_start'].dt.strftime('%Y-%m-%d').tolist(),
                    'y': df['weekly_sales'].tolist(),
                    'marker': {'color': '#1f77b4'}
                }],
                'layout': {
                    'title': 'Weekly Total Sales (Last 7 Weeks)',
                    'xaxis': {'title': 'Week Start'},
                    'yaxis': {'title': 'Total Sales'}
                }
            }

        # --- Top 10 Products by Quantity Sold ---
        df = execute_athena_query("""
            SELECT product_name, SUM(quantity) AS total_quantity
            FROM ecommerce_orders
            GROUP BY product_name
            ORDER BY total_quantity DESC
            LIMIT 10;
        """)
        if not df.empty:
            df['total_quantity'] = pd.to_numeric(df['total_quantity'], errors='coerce')
            charts['top_products'] = {
                'data': [{
                    'type': 'bar',
                    'x': df['total_quantity'].tolist(),
                    'y': df['product_name'].tolist(),
                    'orientation': 'h',
                    'marker': {'color': '#ff7f0e'}
                }],
                'layout': {
                    'title': 'Top 10 Products by Quantity Sold',
                    'xaxis': {'title': 'Quantity'},
                    'yaxis': {
                        'title': 'Product',
                        'automargin': True,
                        'tickfont': {'size': 12}
                    },
                    'margin': {'l': 200}
                }
            }

        # --- Weekly Trends (Grouped Bar) ---
        df = execute_athena_query("""
            SELECT product_name,
                   SUM(quantity) AS total_quantity,
                   DATE_PARSE(order_date, '%Y-%m-%dT%H:%i:%s.%f') AS order_day
            FROM ecommerce_orders
            WHERE order_date >= date_format(current_date - interval '7' day, '%Y-%m-%d')
            GROUP BY product_name, DATE_PARSE(order_date, '%Y-%m-%dT%H:%i:%s.%f')
        """)
        if not df.empty:
            df['total_quantity'] = pd.to_numeric(df['total_quantity'], errors='coerce')
            df['order_day'] = pd.to_datetime(df['order_day'], errors='coerce')
            top_products = df.groupby('product_name')['total_quantity'].sum().nlargest(5).index.tolist()
            charts['trending_items'] = {
                'data': [{
                    'type': 'bar',
                    'x': df[df['product_name'] == p]['order_day'].dt.strftime('%Y-%m-%d').tolist(),
                    'y': df[df['product_name'] == p]['total_quantity'].tolist(),
                    'name': p
                } for p in top_products],
                'layout': {
                    'title': 'Weekly Trends',
                    'barmode': 'group',
                    'xaxis': {'title': 'Date'},
                    'yaxis': {'title': 'Quantity Sold'}
                }
            }

        # --- Weekly Order Status Trend (Stacked Bar) ---
        df = execute_athena_query("""
            SELECT 
                date_trunc('week', DATE_PARSE(order_date, '%Y-%m-%dT%H:%i:%s.%f')) AS week,
                status,
                COUNT(*) AS order_count
            FROM ecommerce_orders
            GROUP BY 1, 2
            ORDER BY week;
        """)
        if not df.empty:
            df['order_count'] = pd.to_numeric(df['order_count'], errors='coerce')
            df['week'] = pd.to_datetime(df['week'], errors='coerce')

            charts['stacked_orders'] = {
                'data': [],
                'layout': {
                    'title': 'Weekly Order Status Trend',
                    'barmode': 'stack',
                    'xaxis': {'title': 'Week'},
                    'yaxis': {'title': 'Order Count'}
                }
            }

            for status in df['status'].unique():
                subset = df[df['status'] == status]
                charts['stacked_orders']['data'].append({
                    'type': 'bar',
                    'name': status,
                    'x': subset['week'].dt.strftime('%Y-%m-%d').tolist(),
                    'y': subset['order_count'].tolist()
                })

    except Exception as e:
        logger.error(f"Error preparing charts: {e}")

    return charts
