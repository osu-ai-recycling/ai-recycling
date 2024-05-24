from flask import Flask, request, jsonify
from pymongo import MongoClient
import mlflow
from datetime import datetime
import zipfile
from bson.objectid import ObjectId
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import io
from random import shuffle
import uuid
from dotenv import load_dotenv, find_dotenv




app = Flask(__name__)

# Load environment variables from aws.env file
dotenv_path = find_dotenv('aws.env')
load_dotenv(dotenv_path)

# Debugging: print loaded environment variables
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
print("AWS_SECRET_ACCESS_KEY:", os.getenv('AWS_SECRET_ACCESS_KEY'))

# Connect to MongoDB
client = MongoClient("mongodb+srv://joonyuan:Bokuben69!@airecycling.kspjt.mongodb.net/")
db = client['AiRecycling']
collection = db['images']  # This accesses the 'images' collection within the 'AiRecycling' database

# Initialize the S3 client using environment variables
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
bucket_name = 'test-api-bucket123'


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


def extract_zip(zip_data):
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
        zip_file.extractall('/tmp/hpc_data_joon')
        for file_name in zip_file.namelist():
            yield file_name


def upload_to_s3(file_path, s3_path):
    try:
        s3_client.upload_file(file_path, bucket_name, s3_path)
        print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_path}")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {str(e)}")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")


def create_s3_directories():
    directories = [
        'test/images/', 'test/labels/',
        'training/images/', 'training/labels/',
        'validation/images/', 'validation/labels/'
    ]
    for directory in directories:
        try:
            s3_client.put_object(Bucket=bucket_name, Key=(directory))
            print(f"Created directory s3://{bucket_name}/{directory}")
        except Exception as e:
            print(f"Error creating directory: {str(e)}")


@app.route('/process-zip/<file_id>', methods=['GET'])
def process_zip(file_id):
    file_data = collection.find_one({'_id': ObjectId(file_id)})
    if not file_data:
        return jsonify({'error': 'File not found'}), 404

    extracted_files = list(extract_zip(file_data['data']))

    # Create directories in S3
    create_s3_directories()

    # Distribute files into test, training, and validation
    jpg_files = [f for f in extracted_files if f.endswith('.jpg')]
    shuffle(jpg_files)
    total_files = len(jpg_files)
    test_split = int(total_files * 0.8)
    train_split = int(total_files * 0.1)
    
    test_files = jpg_files[:test_split]
    train_files = jpg_files[test_split:test_split + train_split]
    validation_files = jpg_files[test_split + train_split:]

    def upload_files_to_s3(files, dest_images, dest_labels):
        for jpg_file in files:
            label_file = jpg_file.replace('images/', 'labels/').replace('.jpg', '.txt')
            src_img_path = os.path.join('/tmp/hpc_data_joon', jpg_file)
            src_lbl_path = os.path.join('/tmp/hpc_data_joon', label_file)
            dest_img_path = os.path.join(dest_images, os.path.basename(jpg_file))
            dest_lbl_path = os.path.join(dest_labels, os.path.basename(label_file))

            # Upload to S3
            upload_to_s3(src_img_path, dest_img_path)
            upload_to_s3(src_lbl_path, dest_lbl_path)

    upload_files_to_s3(test_files, 'test/images/', 'test/labels/')
    upload_files_to_s3(train_files, 'training/images/', 'training/labels/')
    upload_files_to_s3(validation_files, 'validation/images/', 'validation/labels/')

    return jsonify({'status': 'Processing and uploading to S3 completed successfully'}), 200

  
if __name__ == '__main__':
    app.run(debug=True)
