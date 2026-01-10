import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './RiyadhMap.css';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom marker icons by type
const createIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 2px solid white;
      box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -24]
  });
};

const typeColors = {
  landmark: '#e74c3c',
  mall: '#3498db',
  road: '#f39c12',
  district: '#27ae60',
  custom: '#9b59b6'
};

// Component to handle map center updates
function MapController({ center }) {
  const map = useMap();
  
  useEffect(() => {
    if (center) {
      map.flyTo(center, map.getZoom());
    }
  }, [center, map]);
  
  return null;
}

function RiyadhMap({ locations, selectedLocation, onLocationClick }) {
  const [mapCenter, setMapCenter] = useState([24.7136, 46.6753]);
  const [mapZoom] = useState(12);

  useEffect(() => {
    if (selectedLocation) {
      setMapCenter([selectedLocation.lat, selectedLocation.lng]);
    }
  }, [selectedLocation]);

  return (
    <div className="map-wrapper">
      <MapContainer 
        center={mapCenter} 
        zoom={mapZoom} 
        className="map-container"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapController center={selectedLocation ? [selectedLocation.lat, selectedLocation.lng] : null} />
        
        {locations.map((location) => (
          <Marker 
            key={location.id}
            position={[location.lat, location.lng]}
            icon={createIcon(typeColors[location.type] || typeColors.custom)}
            eventHandlers={{
              click: () => onLocationClick && onLocationClick(location)
            }}
          >
            <Popup>
              <div className="popup-content">
                <h3>{location.name}</h3>
                <p><strong>Type:</strong> {location.type}</p>
                <p><strong>Coordinates:</strong></p>
                <p>Lat: {location.lat.toFixed(4)}</p>
                <p>Lng: {location.lng.toFixed(4)}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      <div className="map-legend">
        <h4>Legend</h4>
        {Object.entries(typeColors).map(([type, color]) => (
          <div key={type} className="legend-item">
            <span 
              className="legend-color" 
              style={{ backgroundColor: color }}
            ></span>
            <span className="legend-label">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RiyadhMap;
