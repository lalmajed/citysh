import React, { useEffect, useRef, useState } from 'react';
import './RiyadhMap.css';

// Marker colors by type
const typeColors = {
  landmark: '#e74c3c',
  mall: '#3498db',
  road: '#f39c12',
  district: '#27ae60',
  custom: '#9b59b6'
};

function RiyadhMap({ locations, selectedLocation, onLocationClick }) {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [infoWindow, setInfoWindow] = useState(null);

  // Load Google Maps script
  useEffect(() => {
    // Check if script already loaded
    if (window.google && window.google.maps) {
      initMap();
      return;
    }

    // Load the keyless Google Maps API
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/gh/somanchiu/Keyless-Google-Maps-API@v7.1/mapsJavaScriptAPI.js';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    // Wait for Google Maps to load
    const checkGoogleMaps = setInterval(() => {
      if (window.google && window.google.maps) {
        clearInterval(checkGoogleMaps);
        initMap();
      }
    }, 100);

    return () => {
      clearInterval(checkGoogleMaps);
    };
  }, []);

  // Initialize the map
  const initMap = () => {
    if (!mapRef.current || map) return;

    const googleMap = new window.google.maps.Map(mapRef.current, {
      center: { lat: 24.7136, lng: 46.6753 }, // Riyadh center
      zoom: 12,
      styles: [
        {
          featureType: 'poi',
          elementType: 'labels',
          stylers: [{ visibility: 'off' }]
        }
      ],
      mapTypeControl: true,
      streetViewControl: true,
      fullscreenControl: true,
      zoomControl: true
    });

    const iw = new window.google.maps.InfoWindow();
    setInfoWindow(iw);
    setMap(googleMap);
  };

  // Create custom marker icon
  const createMarkerIcon = (color) => {
    return {
      path: window.google.maps.SymbolPath.CIRCLE,
      fillColor: color,
      fillOpacity: 1,
      strokeColor: '#ffffff',
      strokeWeight: 2,
      scale: 10
    };
  };

  // Update markers when locations or map changes
  useEffect(() => {
    if (!map || !window.google) return;

    // Clear existing markers
    markers.forEach(marker => marker.setMap(null));

    // Create new markers
    const newMarkers = locations.map(location => {
      const marker = new window.google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: map,
        title: location.name,
        icon: createMarkerIcon(typeColors[location.type] || typeColors.custom),
        animation: window.google.maps.Animation.DROP
      });

      // Add click listener
      marker.addListener('click', () => {
        if (infoWindow) {
          infoWindow.setContent(`
            <div style="padding: 10px; min-width: 150px;">
              <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 16px;">${location.name}</h3>
              <p style="margin: 4px 0; color: #7f8c8d; font-size: 13px;"><strong>Type:</strong> ${location.type}</p>
              <p style="margin: 4px 0; color: #7f8c8d; font-size: 13px;"><strong>Lat:</strong> ${location.lat.toFixed(4)}</p>
              <p style="margin: 4px 0; color: #7f8c8d; font-size: 13px;"><strong>Lng:</strong> ${location.lng.toFixed(4)}</p>
            </div>
          `);
          infoWindow.open(map, marker);
        }
        if (onLocationClick) {
          onLocationClick(location);
        }
      });

      return marker;
    });

    setMarkers(newMarkers);
  }, [map, locations, infoWindow, onLocationClick]);

  // Pan to selected location
  useEffect(() => {
    if (!map || !selectedLocation) return;

    map.panTo({ lat: selectedLocation.lat, lng: selectedLocation.lng });
    map.setZoom(15);

    // Find and bounce the selected marker
    const selectedMarker = markers.find(marker => 
      marker.getTitle() === selectedLocation.name
    );
    
    if (selectedMarker) {
      selectedMarker.setAnimation(window.google.maps.Animation.BOUNCE);
      setTimeout(() => {
        selectedMarker.setAnimation(null);
      }, 2000);
    }
  }, [selectedLocation, map, markers]);

  return (
    <div className="map-wrapper">
      <div ref={mapRef} className="map-container"></div>
      
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
