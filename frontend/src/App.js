import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const API_KEY = 'sk-3d1125eb82f5404aa353333b5ff82740'; // 🔐 Replace with your actual API key

const App = () => {
  const [images, setImages] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Handle file input
  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    const validatedError = validateImages(files);
    if (validatedError) {
      setError(validatedError);
      setImages([]);
    } else {
      // Attach preview URLs
      const filesWithPreview = files.map((file) => {
        file.preview = URL.createObjectURL(file);
        return file;
      });
      setError(null);
      setImages(filesWithPreview);
    }
  };

  // ✅ Validate file types and sizes
  const validateImages = (files) => {
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    const maxSize = 5 * 1024 * 1024; // 5MB

    for (let file of files) {
      if (!validTypes.includes(file.type)) {
        return `Unsupported file type: ${file.name}. Only JPEG, PNG, and GIF are allowed.`;
      }
      if (file.size > maxSize) {
        return `File size too large: ${file.name}. Max size is 5MB.`;
      }
    }
    return null;
  };

  // ✅ Upload to backend
  const uploadImages = async () => {
    if (images.length === 0) return;

    const formData = new FormData();
    images.forEach((img) => formData.append('images', img));

    try {
      setLoading(true);
      const response = await axios.post('http://localhost:5000/api/upload', formData, {
        headers: {
          'X-API-KEY': API_KEY,
          'Content-Type': 'multipart/form-data',
        },
      });
      setCatalog(response.data);
      setImages([]);
    } catch (err) {
      setError('Upload failed. Please try again.');
      console.error('Upload failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Fetch full catalog
  const fetchCatalog = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/catalog', {
        headers: {
          'X-API-KEY': API_KEY,
        },
      });
      setCatalog(response.data);
    } catch (err) {
      setError('Failed to fetch catalog. Please try again.');
      console.error('Fetch failed:', err);
    }
  };

  // ✅ Cleanup previews
  useEffect(() => {
    return () => {
      images.forEach((img) => URL.revokeObjectURL(img.preview));
    };
  }, [images]);

  useEffect(() => {
    fetchCatalog();
  }, []);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">SmartCatalog AI</h1>

      {/* Image upload input */}
      <input
        type="file"
        accept="image/*"
        onChange={handleImageChange}
        className="mb-6 border p-2 rounded"
        multiple
      />

      {/* Image previews */}
      {images.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold">Preview</h3>
          <div className="flex flex-wrap justify-start gap-4">
  {images.map((image, index) => (
    <div key={index} className="flex-shrink-0 w-[120px] h-[120px] relative">
      <img
        src={image.preview}
        alt={`Preview ${index}`}
        className="w-full h-full object-cover rounded shadow"
      />
      <p className="absolute bottom-0 left-0 text-xs bg-black bg-opacity-70 text-white p-1 w-full text-center truncate">
        {image.name}
      </p>
    </div>
  ))}
</div>

        </div>
      )}

      {/* Show errors */}
      {error && (
        <div className="mb-6 text-center text-red-500 font-semibold">
          <p>{error}</p>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={uploadImages}
        className="mb-6 bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
        disabled={loading || images.length === 0}
      >
        {loading ? 'Uploading...' : 'Upload Images'}
      </button>

      {/* Catalog Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {catalog.length === 0 && !loading && (
          <p className="text-center text-gray-500">No items in the catalog.</p>
        )}
        {catalog.map((item, index) => (
          <div key={index} className="border p-4 rounded shadow-lg">
            <img
              src={item.image_url}
              alt={item.name}
              className="w-full h-48 object-cover mb-2 rounded"
            />
            <h2 className="text-lg font-semibold">{item.name}</h2>
            <p className="text-sm mb-2">{item.description}</p>
            <ul className="text-sm">
              {Object.entries(item.specifications).map(([key, value], i) => (
                <li key={i}>
                  <strong>{key}:</strong> {value}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
