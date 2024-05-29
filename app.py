from fastapi import FastAPI
import pickle
from pydantic import BaseModel
from typing import List
from sklearn.preprocessing import MinMaxScaler

app = FastAPI(title="Customer Churn")

class CustomerChurn(BaseModel):
    gender: float # 0, 1 atau 2
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
    global model
    model = pickle.load(pickler)
    
@app.post("/predict")
def predict_customer_churn(new_customers: List[CustomerChurn]):
    data = [[customer.num_of_purchases, customer.years_as_customer,
           customer.total_spend, customer.average_transaction_amount, customer.gender]
          for customer in new_customers]

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)
    results = model.predict(scaled_data).tolist()
    return {"result":results}