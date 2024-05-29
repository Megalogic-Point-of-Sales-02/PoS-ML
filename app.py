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
def predict_customer_churn(new_customers: List[CustomerChurn]):
    data = [[customer.num_of_purchases, customer.years_as_customer,
           customer.total_spend, customer.average_transaction_amount, customer.gender]
          for customer in new_customers]

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)
    results = churn.predict(scaled_data).tolist()
    return {"result":results}

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