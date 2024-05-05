from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
import mlflow
from datetime import datetime
import zipfile
from bson.objectid import ObjectId
import mlflow
import os

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://joonyuan:Bokuben69!@airecycling.kspjt.mongodb.net/")
db = client['AiRecycling']
collection = db['images']  #This accesses the 'images' collection within the 'AiRecycling' database, collection holds the reference to our images collection. this will let us perform actions like insert,update etc...

@app.route('/upload', methods=['POST'])
def upload_image():
    image = request.files['image']  #Assume JPEG image file
    #Use current datetime as a suffix for the image filename
    filename = f"{datetime.datetime.now().isoformat()}-{image.filename}"
    image_id = collection.insert_one({'filename': filename, 'data': image.read()}).inserted_id
    return jsonify({'id': str(image_id), 'status': 'uploaded'}), 200

@app.route('/upload-zip', methods=['POST'])
def upload_zip():
    if 'image-zip' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image-zip']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Checking if file is a zip file
    if not zipfile.is_zipfile(file):
        return jsonify({'error': 'Uploaded file is not a zip'}), 400

    # Extract zip file and store each image with datetime suffix in filename
    with zipfile.ZipFile(file, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.lower().endswith('.jpg'):
                image_data = zip_ref.read(file_info.filename)
                datetime_suffix = datetime.datetime.now().isoformat()
                new_filename = f"{datetime_suffix}-{file_info.filename}"
                document = {
                    'filename': new_filename,
                    'data': image_data  # Storing raw bytes
                }
                collection.insert_one(document)

    return jsonify({'status': 'All images uploaded successfully'}), 200
@app.route('/update/<id>', methods=['PUT'])
def update_image(id):
    image = request.files['image']
    result = collection.update_one({'_id': id}, {'$set': {'data': image.read()}})
    if result.modified_count:
        return jsonify({'id': id, 'status': 'updated'}), 200
    else:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/images/<id>', methods=['GET'])
def get_image(id):
    image = collection.find_one({'_id': id})
    if image:
        return image['data'], 200
    else:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/image/<id>')
def serve_image(id):
    try:
        # Convert id from string to ObjectId
        object_id = ObjectId(id)
    except Exception as e:
        return 'Invalid ID format', 400

    image_document = collection.find_one({'_id': object_id})
    if image_document:
        response = make_response(image_document['data'])
        response.headers.set('Content-Type', 'image/jpeg')
        return response
    else:
        return 'Image not found', 404
    
mlflow.set_tracking_uri("http://76.144.70.64:5000/")
client = mlflow.tracking.MlflowClient()

# Specify the experiment ID
experiment_id = "0"  # Replace "0" with the actual ID of your experiment

current_directory = os.path.dirname(os.path.abspath(__file__))

# Access a folder at the same level as the current directory
folder_path = os.path.join(current_directory, 'best_run')

# Max-heap to store runs with their mAP values
max_heap = []

# Function to read the best model information from the text file
def read_best_model_info():
    best_model_info = {}
    try:
        with open(os.path.join(folder_path, 'best_run_info.txt'), 'r') as file:
            lines = file.readlines()
            if lines:
                best_model_info['run_id'] = lines[0].split(': ')[1].strip()
                best_model_info['mAP'] = float(lines[1].split(': ')[1].strip())
                best_model_info['datetime'] = lines[2].split(': ')[1].strip()
    except Exception as e:
        print(f"Error reading from file: {e}")
    return best_model_info

# Function to update the best model information in the text file
def update_best_model_info(run_id, mAP, run_datetime):
    try:
        with open(os.path.join(folder_path, 'best_run_info.txt'), 'w') as file:
            file.write(f'Best Run ID: {run_id}\n')
            file.write(f'mAP Value: {mAP}\n')
            file.write(f'Datetime: {run_datetime}\n')
    except Exception as e:
        print(f"Error writing to file: {e}")

# Function to maintain the max-heap property after inserting a new run
def heapify_up(heap, index):
    if index == 0:
        return
    parent_index = (index - 1) // 2
    if heap[index]['mAP'] > heap[parent_index]['mAP']:
        heap[index], heap[parent_index] = heap[parent_index], heap[index]
        heapify_up(heap, parent_index)

# Function to maintain the max-heap property after removing the maximum element
def heapify_down(heap, index):
    left_child_index = 2 * index + 1
    right_child_index = 2 * index + 2
    largest_index = index
    if left_child_index < len(heap) and heap[left_child_index]['mAP'] > heap[largest_index]['mAP']:
        largest_index = left_child_index
    if right_child_index < len(heap) and heap[right_child_index]['mAP'] > heap[largest_index]['mAP']:
        largest_index = right_child_index
    if largest_index != index:
        heap[index], heap[largest_index] = heap[largest_index], heap[index]
        heapify_down(heap, largest_index)

# Function to add a new run to the max-heap
def add_to_heap(run_id, mAP):
    global max_heap
    max_heap.append({'run_id': run_id, 'mAP': mAP})
    heapify_up(max_heap, len(max_heap) - 1)

# Function to remove the run with the maximum mAP value from the max-heap
def remove_max_from_heap():
    global max_heap
    if not max_heap:
        return None
    max_run = max_heap[0]
    max_heap[0] = max_heap[-1]
    max_heap.pop()
    heapify_down(max_heap, 0)
    return max_run

# Function to find the model with the highest mAP value
def find_best_run(runs):
    global max_heap
    for run in runs:
        run_id = run.info.run_id
        mAP = run.data.metrics.get('mAP_0.5_0.95', None)
        if mAP is not None:
            add_to_heap(run_id, mAP)

    best_run = remove_max_from_heap()
    return best_run['run_id'], best_run['mAP']


@app.route('/best_run', methods=['GET'])
def get_best_run():
    # Read the best model information from the text file
    best_model_info = read_best_model_info()
    
    # Retrieve all runs for the experiment
    runs = client.search_runs(
        experiment_id,
        filter_string="",
        order_by=["metrics.mAP_0.5_0.95 DESC"]
    )

    # Find the model with the highest mAP value
    best_run_id, best_mAP = find_best_run(runs)

    # Compare with the saved best mAP
    if best_mAP > best_model_info['mAP']:
        update_best_model_info(best_run_id, best_mAP, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'best_run_id': best_run_id})

    # Return the ID of the current best model
    return jsonify({'best_run_id': best_model_info['run_id']})


if __name__ == '__main__':
    app.run(debug=True, port=8060)