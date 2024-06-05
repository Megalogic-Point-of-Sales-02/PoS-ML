import pandas as pd
from supabase import create_client, Client
from sklearn.preprocessing import MinMaxScaler
from typing import List


SUPABASE_URL = "https://igswakcuoxvtcwkhczne.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlnc3dha2N1b3h2dGN3a2hjem5lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU0MzY5MDEsImV4cCI6MjAzMTAxMjkwMX0.K0ztyeqlQ4tv-UPyCqRtJSD77B1-PqVM09_5VWJNGQQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cluster_result(segments : List[int]):
    hasil = {0:"Diamond", 2:"Gold", 1:"Silver", 3:"Bronze"}
    return [[hasil.get(segment) for segment in segments]]

def churn_result(churns : List[int]):
    hasil = {0:"Not Churn", 1:"Churn"}
    return [[hasil.get(churn) for churn in churns]]

async def count_RFM(id_customer: int):
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

async def churn_helper(id_customer: int):
    order_table = supabase.table('orders').select("order_date, customer_id, id, sales").execute()
    order_table = order_table.data

    order_table = pd.DataFrame(order_table)
    order_table['order_date'] = pd.to_datetime(order_table['order_date'])
    
    # 'Num_of_Purchases', 'Years_as_Customer', 'Total_Spend', 'Average_Transaction_Amount'
    first_purchased_date = order_table.groupby(["customer_id"], as_index=False)['order_date'].min()
    max_date = pd.Timestamp.now().date()
    first_purchased_date['years_as_customer'] = (pd.Timestamp(max_date) - first_purchased_date['order_date']).dt.total_seconds() / (365 * 24 * 60 * 60)
    
    num_of_purchases = order_table.groupby(['customer_id'], as_index=False)['id'].nunique()
    num_of_purchases.columns = ['customer_id', 'num_of_purchases']
    
    total_spend = order_table.groupby(['customer_id'], as_index=False)['sales'].sum()
    
    average_transaction = pd.merge(num_of_purchases, total_spend, on='customer_id')
    average_transaction['average_sales'] = average_transaction['sales'] / average_transaction['num_of_purchases']
    average_transaction.columns = ['customer_id', 'num_of_purchases', 'total_spend', 'average_spend']
    
    result = pd.merge(first_purchased_date, average_transaction, on='customer_id')

    filtered = result[result['customer_id'] == id_customer]
    gender = await get_gender(id_customer)
    filtered.loc[filtered['customer_id'] == id_customer, 'gender'] = gender
    result_json = filtered.to_json(orient='records')
    return result_json

async def get_gender(customer_id: int) -> int:
    gender_int = {
        "Male": 0,
        "Female": 1,
        "Prefer Not to Say": 2,
    }
    query = supabase.table("customers").select("gender").eq("id", customer_id).single()
    response = query.execute()

    data = response.data
    gender = gender_int.get(data.get("gender"))
    return gender

async def helper_sales_forecast(days: int): 
    order_table = supabase.table('orders').select("order_date, customer_id, id, sales").execute()
    order_table = order_table.data

    order_table = pd.DataFrame(order_table)
    order_table['order_date'] = pd.to_datetime(order_table['order_date'])
    
    total_purchase_by_date = order_table.groupby(['order_date'], as_index=False)['sales'].sum()
    print (total_purchase_by_date)
    
    normalize = MinMaxScaler()
    total_purchase_by_date['sales'] = normalize.fit_transform(total_purchase_by_date[['sales']])
    
    today = pd.Timestamp('today') 

    range = None
    if (days == 0):
        range = today - pd.Timedelta(days=30) 
    elif (days == 1):
        range = today - pd.Timedelta(days=90) 
    elif (days == 2):
        range = today - pd.Timedelta(days=180) 
    elif (days == 3):
        range = today - pd.Timedelta(days=365) 
    else:
        range = today - pd.Timedelta(days=7) 
   
    filtered_df = total_purchase_by_date[total_purchase_by_date['order_date'] >= range]
    filtered_df = filtered_df.sort_values(by='order_date')
    result_json = filtered_df.to_json(orient='records')
    
    
    return result_json, normalize

async def get_stock_total(days: int):
    order_table = supabase.table('orders').select("order_date, quantity").execute()
    order_table = order_table.data

    order_table = pd.DataFrame(order_table)

    sales_data = order_table.groupby(['order_date'], as_index=False)['quantity'].sum()
    sales_data['order_date'] = pd.to_datetime(sales_data['order_date'],format = '%Y-%m-%d')

    normalize = MinMaxScaler()
    sales_data['quantity'] = normalize.fit_transform(sales_data[['quantity']])

    today = pd.Timestamp('today')

    last_date = None
    if(days == 0):
        last_date = today - pd.Timedelta(days=30) 
    elif(days == 1):
        last_date = today - pd.Timedelta(days=90) 
    elif(days == 2):
        last_date = today - pd.Timedelta(days=180) 
    elif(days == 3):
        last_date = today - pd.Timedelta(days=365)
    else:
        last_date = today - pd.Timedelta(days=7) 

    start_date = pd.to_datetime('2024-05-20')
    end_date = pd.to_datetime('2024-05-22')

    filtered_df = sales_data[(sales_data['order_date'] >= start_date) & (sales_data['order_date'] <= end_date)]

    filtered_df = filtered_df.sort_values(by='order_date')

    result_json = filtered_df.to_json(orient='records')

    
    return result_json, normalize