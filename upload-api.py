from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
import datetime
import zipfile
from bson.objectid import ObjectId

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

@app.route('/weights', methods=['GET'])
def compare_models():
    # Implement model comparison logic here
    # For now, return a dummy response
    response = {
        'best_model': 'model_xyz',
        'download_link': 'http://example.com/model_xyz',
        'accuracy': 0.95
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
