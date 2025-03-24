import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const App = () => {
  const [images, setImages] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(false);

  // Handle file input change
  const handleImageChange = (e) => {
    setImages(e.target.files);
  };

  // Upload images to the backend API
  const uploadImages = async () => {
    const formData = new FormData();
    for (let i = 0; i < images.length; i++) {
      formData.append('images', images[i]);
    }
    try {
      setLoading(true);  // Show loading state
      const response = await axios.post('http://localhost:5000/api/upload', formData);
      setCatalog(response.data);  // Update the catalog with the response
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setLoading(false);  // Hide loading state
    }
  };

  // Fetch existing catalog from the backend
  const fetchCatalog = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/catalog');
      setCatalog(response.data);  // Set the catalog from the backend data
    } catch (error) {
      console.error('Fetch failed:', error);
    }
  };

  // Fetch catalog when the component loads
  useEffect(() => {
    fetchCatalog();
  }, []);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Product Catalog Generator</h1>

      <input type="file" multiple onChange={handleImageChange} className="mb-4" />
      <button onClick={uploadImages} className="bg-blue-600 text-white px-4 py-2 rounded mb-6">
        Upload & Generate
      </button>

      {loading && <p>Processing images...</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {catalog.map((item, index) => (
          <div key={index} className="border p-4 rounded shadow">
            <img src={item.image_url} alt="Product" className="w-full h-48 object-cover mb-2" />
            <h2 className="text-lg font-semibold">{item.name}</h2>
            <p className="text-sm mb-2">{item.description}</p>
            <ul className="text-sm">
              {Object.entries(item.specifications).map(([key, value], i) => (
                <li key={i}><strong>{key}:</strong> {value}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
