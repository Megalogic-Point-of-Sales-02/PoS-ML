import os
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client
from sklearn.preprocessing import MinMaxScaler
from typing import List
import numpy as np

load_dotenv() 

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
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

async def helper_sales_forecast(): 
    order_table = supabase.table('orders').select("order_date, customer_id, id, sales").execute()
    order_table = order_table.data

    order_table = pd.DataFrame(order_table)
    order_table['order_date'] = pd.to_datetime(order_table['order_date'])
    
    total_purchase_by_date = order_table.groupby(['order_date'], as_index=False)['sales'].sum()

    
    normalize = MinMaxScaler()
    total_purchase_by_date['sales'] = normalize.fit_transform(total_purchase_by_date[['sales']])
    
    today = pd.Timestamp('today') 
    start = today - pd.Timedelta(days=365) 
    end = today +  pd.Timedelta(days=365)
   
    filtered_df = total_purchase_by_date[total_purchase_by_date['order_date'].dt.date >= start.date()]

    
    date_range = pd.date_range(start=start.date(), end=end.date())
    complete_df = pd.DataFrame(index=date_range, columns=['order_date', 'sales'])
    complete_df['order_date'] = complete_df.index
    complete_df.set_index('order_date', inplace=True)
    complete_df.update(filtered_df.set_index('order_date'))
    complete_df['sales'].fillna(0, inplace=True) #TODO: Fill with median 
    
    complete_df = complete_df.sort_index(ascending=True)

    
    sales_only = complete_df['sales'].values
    sales_only = np.array(sales_only.reshape(-1, 1))
    
    sales_predict = []
    
    for i in range(365, len(sales_only)):
        sales_predict.append(sales_only[i-365:i, 0])
    
    sales_predict = np.array(sales_predict)
    return sales_predict, normalize

async def get_stock_total():
    order_table = supabase.table('orders').select("order_date, quantity").execute()
    order_table = order_table.data

    order_table = pd.DataFrame(order_table)
    order_table['order_date'] = pd.to_datetime(order_table['order_date'])

    sales_data = order_table.groupby(['order_date'], as_index=False)['quantity'].sum()
    
    normalize = MinMaxScaler()
    sales_data['quantity'] = normalize.fit_transform(sales_data[['quantity']])

    today = pd.Timestamp('today') 
    start = today - pd.Timedelta(days=365) 
    end = today +  pd.Timedelta(days=365)

    filtered_df = sales_data[sales_data['order_date'].dt.date >= start.date()]

    date_range = pd.date_range(start=start.date(), end=end.date())
    complete_df = pd.DataFrame(index=date_range, columns=['order_date', 'quantity'])
    complete_df['order_date'] = complete_df.index
    complete_df.set_index('order_date', inplace=True)
    complete_df.update(filtered_df.set_index('order_date'))
    complete_df['quantity'].fillna(0, inplace=True)

    complete_df = complete_df.sort_index(ascending=True)
    
    qty_only = complete_df['quantity'].values
    qty_only = np.array(qty_only.reshape(-1, 1))
    
    predict = []
    
    for i in range(365, len(qty_only)):
        predict.append(qty_only[i-365:i, 0])
    
    predict = np.array(predict)
    
    return predict, normalize