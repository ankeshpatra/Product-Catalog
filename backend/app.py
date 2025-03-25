import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from werkzeug.utils import secure_filename
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import easyocr
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Google API keys
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
GOOGLE_CX = "YOUR_SEARCH_ENGINE_ID"

# Database
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
db.commit()

# BLIP + OCR
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
reader = easyocr.Reader(['en'])

def generate_image_description(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt")
    output = model.generate(**inputs)
    return processor.decode(output[0], skip_special_tokens=True)

def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()
        snippets = [item.get("snippet", "") for item in results.get("items", [])]
        return " | ".join(snippets[:3])
    return "No data found."

def generate_catalog_data(image_path):
    description = generate_image_description(image_path)
    extracted_text = extract_text_from_image(image_path)
    google_data = google_search(description)

    specs = {
        "Brand": "",
        "Model Name": "",
        "Price": "",
        "Color": "Varied",
        "Material": "Synthetic",
        "Details": google_data
    }

    for word in extracted_text.split():
        if word.lower().startswith("model"):
            specs["Model Name"] = word
        elif "$" in word or word.replace(",", "").replace(".", "").isdigit():
            specs["Price"] = word
        elif word.isalpha() and len(word) > 3 and not specs["Brand"]:
            specs["Brand"] = word

    return {
        "name": f"Product: {description[:30]}...",
        "description": f"{description} | OCR: {extracted_text}",
        "specifications": specs
    }

@app.route('/api/upload', methods=['POST'])
def upload_images():
    uploaded_files = request.files.getlist("images")
    if not uploaded_files:
        return jsonify({'error': 'No files uploaded'}), 400

    results = []

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            data = generate_catalog_data(file_path)
            cursor.execute('''
                INSERT INTO catalog (image_url, name, description, specifications)
                VALUES (%s, %s, %s, %s)
            ''', (
                f"/static/{filename}",
                data['name'],
                data['description'],
                json.dumps(data['specifications'])
            ))
            db.commit()

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
        try:
            specs = json.loads(specifications)
        except:
            specs = {}

        results.append({
            "image_url": image_url,
            "name": name,
            "description": description,
            "specifications": specs
        })

    return jsonify(results)

@app.route('/static/<path:filename>')
def serve_static_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
