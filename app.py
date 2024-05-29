from fastapi import FastAPI
import pickle, helper, os, json
from pydantic import BaseModel
from typing import List
from sklearn.preprocessing import MinMaxScaler

app = FastAPI(title="Customer Churn")

class CustomerChurn(BaseModel):
    gender: float 
    total_spend: float
    years_as_customer: float
    num_of_purchases: float
    average_transaction_amount: float

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
    return {"result": results}


@app.get("/cluster")
def perform(id_cust: int):
    data = helper.count_RFM(id_cust)
    data = json.loads(data)

    if (len(data) == 0):
        return {"segmentation": "-"} 
    data = data[0]
    dataset = [[data['days_since_last_purchased'], data['total_transaction'], data['total_spend'], data['average_spend']]]

    cluster = kmeans.predict(dataset).tolist()
    label = "-"
    if len(cluster) > 0: 
        label = helper.cluster_result(cluster[0])
    
    return {"segmentation":label}