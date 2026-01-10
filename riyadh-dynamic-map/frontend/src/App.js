import React, { useState, useEffect } from 'react';
import { RiyadhMap } from './components/Map';
import { Sidebar } from './components/Sidebar';
import { getLocations, addLocation } from './services/api';
import './App.css';

function App() {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch locations from backend
  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      const response = await getLocations();
      if (response.success) {
        setLocations(response.data);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch locations:', err);
      setError('Failed to connect to backend. Using default data.');
      // Fallback to default data if backend is not available
      setLocations([
        { id: 1, name: "Kingdom Centre Tower", lat: 24.7111, lng: 46.6747, type: "landmark" },
        { id: 2, name: "Al Faisaliyah Tower", lat: 24.6901, lng: 46.6855, type: "landmark" },
        { id: 3, name: "Riyadh Park Mall", lat: 24.7636, lng: 46.6340, type: "mall" },
        { id: 4, name: "King Fahd Road", lat: 24.7136, lng: 46.6753, type: "road" },
        { id: 5, name: "Al Muhammadiyah District", lat: 24.7944, lng: 46.6847, type: "district" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
  };

  const handleAddLocation = async (newLocation) => {
    try {
      const response = await addLocation(newLocation);
      if (response.success) {
        setLocations([...locations, response.data]);
      }
    } catch (err) {
      console.error('Failed to add location:', err);
      // Add locally if backend fails
      const localLocation = {
        id: Date.now(),
        ...newLocation,
        lat: parseFloat(newLocation.lat),
        lng: parseFloat(newLocation.lng)
      };
      setLocations([...locations, localLocation]);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader"></div>
        <p>Loading Riyadh Map...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <Sidebar
        locations={locations}
        onLocationSelect={handleLocationSelect}
        onAddLocation={handleAddLocation}
        selectedLocation={selectedLocation}
      />
      <main className="main-content">
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}
        <RiyadhMap
          locations={locations}
          selectedLocation={selectedLocation}
          onLocationClick={handleLocationSelect}
        />
      </main>
    </div>
  );
}

export default App;
