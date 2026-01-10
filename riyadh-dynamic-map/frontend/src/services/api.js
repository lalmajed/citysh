import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Get all locations
export const getLocations = async () => {
  try {
    const response = await api.get('/locations');
    return response.data;
  } catch (error) {
    console.error('Error fetching locations:', error);
    throw error;
  }
};

// Get location by ID
export const getLocationById = async (id) => {
  try {
    const response = await api.get(`/locations/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching location:', error);
    throw error;
  }
};

// Get locations by type
export const getLocationsByType = async (type) => {
  try {
    const response = await api.get(`/locations/type/${type}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching locations by type:', error);
    throw error;
  }
};

// Add new location
export const addLocation = async (locationData) => {
  try {
    const response = await api.post('/locations', locationData);
    return response.data;
  } catch (error) {
    console.error('Error adding location:', error);
    throw error;
  }
};

// Search locations
export const searchLocations = async (query) => {
  try {
    const response = await api.get('/search', { params: { q: query } });
    return response.data;
  } catch (error) {
    console.error('Error searching locations:', error);
    throw error;
  }
};

// Get map bounds
export const getMapBounds = async () => {
  try {
    const response = await api.get('/bounds');
    return response.data;
  } catch (error) {
    console.error('Error fetching bounds:', error);
    throw error;
  }
};

// Health check
export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('API health check failed:', error);
    throw error;
  }
};

export default api;
