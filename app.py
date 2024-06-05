from fastapi import FastAPI
import pickle, helper, os, json
from pydantic import BaseModel
from typing import List
from sklearn.preprocessing import MinMaxScaler
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
from tensorflow  import keras
from keras import losses
import math

app = FastAPI(title="Customer Churn")

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pointofsales-02-at2vbh6rta-as.a.run.app", "216.239.32.53"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomerChurn(BaseModel):
    gender: float 
    total_spend: float
    years_as_customer: float
    num_of_purchases: float
    average_transaction_amount: float

class CustomerSegment(BaseModel):
    days_since_last_purchased: float 
    total_transaction: float
    total_spend: float
    average_spend: float

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.on_event("startup")
def load_model():
    with open("model_nb.pkl", "rb") as pickler:
        global churn
        churn = pickle.load(pickler)

    with open("kmeans.pkl", "rb") as pickler:
        global kmeans
        kmeans = pickle.load(pickler)
    
@app.post("/predict")
async def predict_customer_churn(customers: List[int]):
    
    data_helper = []
    for customer_id in customers:
        customer_temp = await helper.churn_helper(customer_id)
        customer_temp = json.loads(customer_temp)
        customer_temp = customer_temp[0]
        
        customer_total_spend = customer_temp["total_spend"]
        customer_years_as_customer = customer_temp["years_as_customer"]
        customer_num_of_purchases = customer_temp["num_of_purchases"]
        customer_avg_transaction = customer_temp["average_spend"]
        customer_gender = customer_temp["gender"]
        
        customerChurn = CustomerChurn(
            gender= customer_gender,
            total_spend= customer_total_spend,
            years_as_customer= customer_years_as_customer,
            num_of_purchases= customer_num_of_purchases,
            average_transaction_amount= customer_avg_transaction,
        )
        data_helper.append(customerChurn)
        
    data = [[customer.num_of_purchases, customer.years_as_customer,
           customer.total_spend, customer.average_transaction_amount, customer.gender]
          for customer in data_helper]
    
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)
    results = churn.predict(scaled_data).tolist()
    results = helper.churn_result(results)
    return {"result": results}


@app.post("/cluster")
async def perform(customers: List[int]):
    data_helper = []
    for cust_id in  customers:
        temp = await helper.count_RFM(cust_id)
        temp = json.loads(temp)
        temp = temp[0]

        customer = CustomerSegment(
            days_since_last_purchased= temp["days_since_last_purchased"],
            total_transaction= temp["total_transaction"],
            total_spend= temp["total_spend"],
            average_spend= temp["average_spend"],
        )
        data_helper.append(customer)

    data = [[customer.days_since_last_purchased, customer.total_transaction,
           customer.total_spend, customer.average_spend]
          for customer in data_helper]

    cluster = kmeans.predict(data).tolist()
    cluster = helper.cluster_result(cluster)
    
    return {"segmentation":cluster}

@app.post("/sales_forecast")
async def sales_forecast(days: int):
    model = tf.keras.models.load_model("sales_forecast.keras", compile=False)
    data, normalize = await helper.helper_sales_forecast(days)
    
    forecast_sales = np.reshape(data, (data.shape[0], data.shape[1], 1 ))
    result = model.predict(forecast_sales).ravel()
    
    predictions = normalize.inverse_transform(result.reshape(-1, 1)).ravel().tolist()
    return {"result": predictions}
    
@app.post("/stock-sales")
async def stock_sales(days: int):
    data, normalize = await helper.get_stock_total(days)
    data_json = json.loads(data)

    temp = [[item["quantity"]] for item in data_json]

    data_arr = np.array(temp, dtype="float").reshape(len(data_json), 1)

    model = tf.keras.models.load_model("stock_sales_forecast.keras", compile=False)
    result = model.predict(data_arr)

    predictions = normalize.inverse_transform(result)
    predictions = [math.ceil(value) for value in predictions.flatten()]
    
    return {"result": predictions}

