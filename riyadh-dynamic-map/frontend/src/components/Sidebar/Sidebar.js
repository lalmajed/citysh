import React, { useState } from 'react';
import './Sidebar.css';

function Sidebar({ locations, onLocationSelect, onAddLocation, selectedLocation }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newLocation, setNewLocation] = useState({
    name: '',
    lat: '',
    lng: '',
    type: 'custom'
  });

  const filteredLocations = locations.filter(loc =>
    loc.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newLocation.name && newLocation.lat && newLocation.lng) {
      onAddLocation(newLocation);
      setNewLocation({ name: '', lat: '', lng: '', type: 'custom' });
      setShowAddForm(false);
    }
  };

  const typeColors = {
    landmark: '#e74c3c',
    mall: '#3498db',
    road: '#f39c12',
    district: '#27ae60',
    custom: '#9b59b6'
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🗺️ Riyadh Map</h2>
        <p className="subtitle">Dynamic Location Explorer</p>
      </div>

      <div className="search-container">
        <input
          type="text"
          placeholder="Search locations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="location-list">
        <div className="list-header">
          <h3>Locations ({filteredLocations.length})</h3>
          <button 
            className="add-btn"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? '✕' : '+'}
          </button>
        </div>

        {showAddForm && (
          <form className="add-form" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Location name"
              value={newLocation.name}
              onChange={(e) => setNewLocation({...newLocation, name: e.target.value})}
              required
            />
            <div className="coord-inputs">
              <input
                type="number"
                placeholder="Latitude"
                step="any"
                value={newLocation.lat}
                onChange={(e) => setNewLocation({...newLocation, lat: e.target.value})}
                required
              />
              <input
                type="number"
                placeholder="Longitude"
                step="any"
                value={newLocation.lng}
                onChange={(e) => setNewLocation({...newLocation, lng: e.target.value})}
                required
              />
            </div>
            <select
              value={newLocation.type}
              onChange={(e) => setNewLocation({...newLocation, type: e.target.value})}
            >
              <option value="custom">Custom</option>
              <option value="landmark">Landmark</option>
              <option value="mall">Mall</option>
              <option value="road">Road</option>
              <option value="district">District</option>
            </select>
            <button type="submit" className="submit-btn">Add Location</button>
          </form>
        )}

        <div className="locations">
          {filteredLocations.map((location) => (
            <div
              key={location.id}
              className={`location-item ${selectedLocation?.id === location.id ? 'selected' : ''}`}
              onClick={() => onLocationSelect(location)}
            >
              <div 
                className="location-indicator"
                style={{ backgroundColor: typeColors[location.type] || typeColors.custom }}
              ></div>
              <div className="location-info">
                <h4>{location.name}</h4>
                <span className="location-type">{location.type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-footer">
        <p>Data sourced from Riyadh GIS</p>
      </div>
    </div>
  );
}

export default Sidebar;
