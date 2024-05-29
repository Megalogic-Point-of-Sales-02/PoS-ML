import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler

SUPABASE_URL = "https://igswakcuoxvtcwkhczne.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlnc3dha2N1b3h2dGN3a2hjem5lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU0MzY5MDEsImV4cCI6MjAzMTAxMjkwMX0.K0ztyeqlQ4tv-UPyCqRtJSD77B1-PqVM09_5VWJNGQQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cluster_result(angka : int):
    hasil = {0:"Diamond", 2:"Gold", 1:"Silver", 3:"Bronze"}
    return hasil[angka]

def count_RFM(id_customer: int):
    order_table = supabase.table('orders').select("order_date, customer_id, id, sales").execute()
    order_table = order_table.data

    order_table = pd.DataFrame(order_table)

    order_table['order_date'] = pd.to_datetime(order_table['order_date'])
    last_purchased_date = order_table.groupby(["customer_id"], as_index=False)['order_date'].max()

    max_date = pd.Timestamp.now().date()
    last_purchased_date['days_since_last_purchased'] = (pd.Timestamp(max_date) - last_purchased_date['order_date']).dt.days

    total_transaction = order_table.groupby(['customer_id'], as_index=False)['id'].nunique()
    total_transaction.columns = ['customer_id', 'total_transaction']

    total_spend_per_transaction = order_table.groupby(['customer_id'], as_index=False)['sales'].sum()

    average_transaction = pd.merge(total_transaction, total_spend_per_transaction, on='customer_id')
    average_transaction['average_sales'] = average_transaction['sales'] / average_transaction['total_transaction']
    average_transaction.columns = ['customer_id', 'total_transaction', 'total_spend', 'average_spend']

    result = pd.merge(last_purchased_date, average_transaction, on='customer_id')

    normalize = MinMaxScaler()

    exclude_col = ['customer_id', 'order_date']
    col_to_scale = result.columns.difference(exclude_col)
    merged_data_scaled = result.copy()
    merged_data_scaled[col_to_scale] = normalize.fit_transform(merged_data_scaled[col_to_scale])
    merged_data_scaled = pd.DataFrame(merged_data_scaled, columns=result.columns)

    filtered = merged_data_scaled[merged_data_scaled['customer_id'] == id_customer]
    result_json = filtered.to_json(orient='records')

    return result_json