const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const axios = require('axios');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Sample Riyadh location data - you can replace with your actual data source
const riyadhLocations = [
  { id: 1, name: "Kingdom Centre Tower", lat: 24.7111, lng: 46.6747, type: "landmark" },
  { id: 2, name: "Al Faisaliyah Tower", lat: 24.6901, lng: 46.6855, type: "landmark" },
  { id: 3, name: "Riyadh Park Mall", lat: 24.7636, lng: 46.6340, type: "mall" },
  { id: 4, name: "King Fahd Road", lat: 24.7136, lng: 46.6753, type: "road" },
  { id: 5, name: "Al Muhammadiyah District", lat: 24.7944, lng: 46.6847, type: "district" },
];

// Routes

// Get all locations
app.get('/api/locations', (req, res) => {
  res.json({ success: true, data: riyadhLocations });
});

// Get location by ID
app.get('/api/locations/:id', (req, res) => {
  const location = riyadhLocations.find(loc => loc.id === parseInt(req.params.id));
  if (location) {
    res.json({ success: true, data: location });
  } else {
    res.status(404).json({ success: false, message: 'Location not found' });
  }
});

// Get locations by type
app.get('/api/locations/type/:type', (req, res) => {
  const filtered = riyadhLocations.filter(loc => loc.type === req.params.type);
  res.json({ success: true, data: filtered });
});

// Add new location
app.post('/api/locations', (req, res) => {
  const { name, lat, lng, type } = req.body;
  if (!name || !lat || !lng) {
    return res.status(400).json({ success: false, message: 'Name, lat, and lng are required' });
  }
  
  const newLocation = {
    id: riyadhLocations.length + 1,
    name,
    lat: parseFloat(lat),
    lng: parseFloat(lng),
    type: type || 'custom'
  };
  
  riyadhLocations.push(newLocation);
  res.status(201).json({ success: true, data: newLocation });
});

// Search locations
app.get('/api/search', (req, res) => {
  const { q } = req.query;
  if (!q) {
    return res.json({ success: true, data: riyadhLocations });
  }
  
  const filtered = riyadhLocations.filter(loc => 
    loc.name.toLowerCase().includes(q.toLowerCase())
  );
  res.json({ success: true, data: filtered });
});

// Get bounding box data (for map initialization)
app.get('/api/bounds', (req, res) => {
  res.json({
    success: true,
    data: {
      center: { lat: 24.7136, lng: 46.6753 },
      zoom: 12,
      bounds: {
        north: 24.95,
        south: 24.50,
        east: 46.95,
        west: 46.40
      }
    }
  });
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`🚀 Riyadh Dynamic Map Backend running on port ${PORT}`);
  console.log(`📍 API available at http://localhost:${PORT}/api`);
});
