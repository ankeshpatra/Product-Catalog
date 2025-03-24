from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

app = Flask(__name__)
CORS(app)

# MySQL setup
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123",
    database="catalog"
)
cursor = db.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS catalog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_url VARCHAR(255),
    name VARCHAR(255),
    description TEXT,
    specifications TEXT
)
''')

# Load BLIP-2 model (image-to-text)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_image_description(image_path):
    # Load the image and process it
    raw_image = Image.open(image_path).convert("RGB")
    
    # Prepare inputs for the model
    inputs = processor(raw_image, return_tensors="pt")

    # Generate text description from the image
    output = model.generate(**inputs)
    description = processor.decode(output[0], skip_special_tokens=True)
    
    return description

def generate_catalog_data(image_path):
    # Step 1: Get the description from the image using BLIP-2
    description = generate_image_description(image_path)
    print(f"Generated Image Description: {description}")
    
    # Step 2: Use the description to generate catalog-like information
    # Here, we are assuming a simple mock for the generated product information
    # You can later use a GPT model to improve the text generation.
    catalog_data = {
        "name": f"Product Based on {description[:30]}...",
        "description": description,
        "specifications": {
            "Material": "Synthetic",
            "Color": "Varied",
            "Dimensions": "Standard size"
        }
    }
    
    return catalog_data

@app.route('/api/upload', methods=['POST'])
def upload_images():
    uploaded_files = request.files.getlist("images")
    if not uploaded_files:
        return jsonify({'error': 'No files uploaded'}), 400

    results = []

    for file in uploaded_files:
        filename = file.filename
        file_path = os.path.join('static', filename)
        file.save(file_path)

        try:
            # Generate catalog data using the image
            data = generate_catalog_data(file_path)

            # Insert into the MySQL database
            cursor.execute('''
                INSERT INTO catalog (image_url, name, description, specifications)
                VALUES (%s, %s, %s, %s)
            ''', (
                file_path,
                data['name'],
                data['description'],
                str(data['specifications'])  # Store specifications as a stringified dict
            ))
            db.commit()

            # Append the result to be returned to the frontend
            results.append({
                "image_url": f"/static/{filename}",
                "name": data['name'],
                "description": data['description'],
                "specifications": data['specifications']
            })

        except Exception as e:
            print("Error generating catalog:", str(e))
            continue

    return jsonify(results)

@app.route('/api/catalog', methods=['GET'])
def get_catalog():
    cursor.execute("SELECT image_url, name, description, specifications FROM catalog")
    catalog = cursor.fetchall()
    results = []

    for (image_url, name, description, specifications) in catalog:
        results.append({
            "image_url": image_url,
            "name": name,
            "description": description,
            "specifications": eval(specifications)
        })

    return jsonify(results)

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
