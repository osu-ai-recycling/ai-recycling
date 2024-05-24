import os
from pymongo import MongoClient
from datetime import datetime, timedelta
import mlflow
import time

# MongoDB settings
mongo_conn_str = "mongodb+srv://joonyuan:Bokuben69!@airecycling.kspjt.mongodb.net/"
db_name = "AiRecycling"
coll_name = "images"
experiment_id = "0"

# MLflow settings
mlflow.set_tracking_uri("http://ec2-18-220-114-91.us-east-2.compute.amazonaws.com:5000/")
experiment_name = "Default"
mlflow.set_experiment(experiment_name)

# Connect to MongoDB
mongo_client = MongoClient(mongo_conn_str)
db = mongo_client[db_name]
collection = db[coll_name]
collection_latest = "None"
latest_data = ""

# Function to check time passed since last train
def check_training_time():
    # mlflow_client = mlflow.tracking.MlflowClient()
    runs = mlflow.search_runs(experiment_ids=[experiment_id])
    first_run_name = runs.iloc[0]["tags.mlflow.runName"]
    run_time = datetime.strptime(first_run_name, "%Y-%m-%d_%H-%M-%S")
    if datetime.now() - run_time >= timedelta(hours=24):
        return True
    else:
        return False
    
# print(check_training_time())
# print(collection_latest = collection.find().sort('$natural', -1).limit(1)[0]['filename'])

# Function to check for new data in MongoDB
def check_new_data():
    global latest_data
    collection_latest = collection.find().sort('$natural', -1).limit(1)[0]['filename']
    if latest_data != collection_latest:
        return True
    else:
        return False

# Main loop to run forever
while True:
    if check_training_time() and check_new_data():
        latest_data = collection_latest
        os.system("./hpc_run.sh train --data ../far_west_7_set/data.yaml --weights yolov5s.pt --batch-size 32 --seed 42 --epochs 3")
    else:
        time.sleep(60)
    