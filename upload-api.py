from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
import mlflow
from datetime import datetime
import zipfile
from bson.objectid import ObjectId
import os
import shutil
import paramiko
import io
from random import shuffle

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://joonyuan:Bokuben69!@airecycling.kspjt.mongodb.net/")
db = client['AiRecycling']
collection = db['images']  #This accesses the 'images' collection within the 'AiRecycling' database, collection holds the reference to our images collection. this will let us perform actions like insert,update etc...

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
    
    # Read the ZIP file as binary data
    file.seek(0)  # Reset the file cursor to the beginning
    zip_data = file.read()

    # Store the entire zip file with datetime suffix in filename
    datetime_suffix = datetime.datetime.now().isoformat()
    new_filename = f"{datetime_suffix}-{file.filename}"
    document = {
        'filename': new_filename,
        'data': zip_data  # Storing the entire ZIP file as binary data
    }
    collection.insert_one(document)

    return jsonify({'status': 'ZIP file uploaded successfully'}), 200
    
@app.route('/send-to-hpc', methods=['POST'])
def send_to_hpc():
    zip_id = request.json.get('zip_id')
    if not zip_id:
        return jsonify({'error': 'No ZIP file ID provided'}), 400
    
    # Retrieve the ZIP file from MongoDB
    zip_file = collection.find_one({'_id': ObjectId(zip_id)})
    if not zip_file:
        return jsonify({'error': 'ZIP file not found'}), 404

    # Extract the ZIP file
    zip_data = io.BytesIO(zip_file['data'])
    source_dir = 'temp'  # Directory to extract the ZIP files
    target_dir = 'ai-data'  # Directory to organize files into train/test/validation
    with zipfile.ZipFile(zip_data, 'r') as zip_ref:
        zip_ref.extractall(source_dir)

    # Organize files into the required directory structure
    organize_files(source_dir, target_dir)

    # Send organized files to HPC
    success = send_files_to_hpc(target_dir)

    # Cleanup temporary directories
    shutil.rmtree(source_dir)
    shutil.rmtree(target_dir)

    if success:
        return jsonify({'status': 'Data sent to HPC successfully'}), 200
    else:
        return jsonify({'error': 'Failed to send data to HPC'}), 500

def send_files_to_hpc(target_dir):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('76.144.70.64', username='austin', password='M18RED', port=22)
        sftp = ssh.open_sftp()
        
        # Walk through the directory and upload files
        for dirpath, dirnames, filenames in os.walk(target_dir):
            remote_path = dirpath.replace(target_dir, '/remote/directory/ai-data')
            try:
                sftp.mkdir(remote_path)
            except IOError:
                pass  # Remote directory already exists
            for filename in filenames:
                sftp.put(os.path.join(dirpath, filename), os.path.join(remote_path, filename))
        
        sftp.close()
        ssh.close()
        return True
    except Exception as e:
        print(f"SSH connection error: {e}")
        return False
    

mlflow.set_tracking_uri("http://ec2-18-220-114-91.us-east-2.compute.amazonaws.com:5000/")

# Create an instance of MlflowClient
client = mlflow.tracking.MlflowClient()

# Specify the experiment ID
experiment_id = "0"  # Replace "0" with the actual ID of your experiment

@app.route('/best_run', methods=['GET'])
def get_best_run():
    # Search for runs, ordering by the 'mAP_0.5_0.95' metric in descending order
    # and limiting the result to the top 1 run
    best_run = client.search_runs(
        experiment_id, 
        order_by=["metrics.mAP_0.5_0.95 DESC"], 
        max_results=1
    )[0]
    
    # Extract and return the ID of the best run
    best_run_id = best_run.info.run_id
    return jsonify({'best_run_id': best_run_id})

if __name__ == '__main__':
    app.run(debug=True)


def organize_files(source_dir, target_dir):
    image_files = [f for f in os.listdir(source_dir) if f.endswith('.jpg')]
    label_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]

    # Randomly shuffle the list of images to ensure random distribution
    shuffled_images = list(image_files)
    shuffle(shuffled_images)

    # Calculate the indices for splitting
    total_images = len(shuffled_images)
    train_end = int(0.7 * total_images)  # 70% for training
    test_end = train_end + int(0.15 * total_images)  # 15% for testing

    # Create train, test, validation folders for images and labels
    for phase in ['train', 'test', 'validation']:
        os.makedirs(os.path.join(target_dir, phase, 'images'), exist_ok=True)
        os.makedirs(os.path.join(target_dir, phase, 'labels'), exist_ok=True)

    # Distribute files
    for idx, filename in enumerate(shuffled_images):
        if idx < train_end:
            phase = 'train'
        elif idx < test_end:
            phase = 'test'
        else:
            phase = 'validation'
        
        # Get the basename without extension to find corresponding label file
        basename = os.path.splitext(filename)[0]
        label_file = basename + '.txt'

        # Move image and label files to their respective directories
        shutil.move(os.path.join(source_dir, filename), os.path.join(target_dir, phase, 'images', filename))
        if label_file in label_files:
            shutil.move(os.path.join(source_dir, label_file), os.path.join(target_dir, phase, 'labels', label_file))


if __name__ == '__main__':
    app.run(debug=True, port=8060)