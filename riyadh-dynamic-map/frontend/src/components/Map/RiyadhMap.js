import React, { useEffect, useRef, useState, useCallback } from 'react';
import './RiyadhMap.css';

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
  const [isLoaded, setIsLoaded] = useState(false);

  const initializeMap = useCallback(() => {
    if (!mapRef.current || map) return;

    try {
      const googleMap = new window.google.maps.Map(mapRef.current, {
        center: { lat: 24.7136, lng: 46.6753 },
        zoom: 12,
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true,
        zoomControl: true
      });

      const iw = new window.google.maps.InfoWindow();
      setInfoWindow(iw);
      setMap(googleMap);
      setIsLoaded(true);
    } catch (error) {
      console.error('Error initializing map:', error);
    }
  }, [map]);

  // Load Google Maps script
  useEffect(() => {
    // Define global initMap function that Google Maps expects
    window.initMap = () => {
      initializeMap();
    };

    // Check if already loaded
    if (window.google && window.google.maps && window.google.maps.Map) {
      initializeMap();
      return;
    }

    // Check if script already exists
    const existingScript = document.querySelector('script[src*="Keyless-Google-Maps-API"]');
    if (existingScript) {
      const checkReady = setInterval(() => {
        if (window.google && window.google.maps && window.google.maps.Map) {
          clearInterval(checkReady);
          initializeMap();
        }
      }, 100);
      return () => clearInterval(checkReady);
    }

    // Load the script
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/gh/somanchiu/Keyless-Google-Maps-API@v7.1/mapsJavaScriptAPI.js';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    const checkGoogleMaps = setInterval(() => {
      if (window.google && window.google.maps && window.google.maps.Map) {
        clearInterval(checkGoogleMaps);
        initializeMap();
      }
    }, 200);

    return () => {
      clearInterval(checkGoogleMaps);
    };
  }, [initializeMap]);

  const createMarkerIcon = (color) => {
    if (!window.google || !window.google.maps) return null;
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
    if (!map || !window.google || !window.google.maps || !isLoaded) return;

    // Clear existing markers
    markers.forEach(marker => {
      if (marker && marker.setMap) {
        marker.setMap(null);
      }
    });

    // Create new markers
    const newMarkers = locations.map(location => {
      const icon = createMarkerIcon(typeColors[location.type] || typeColors.custom);
      
      const marker = new window.google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: map,
        title: location.name,
        icon: icon
      });

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
  }, [map, locations, infoWindow, onLocationClick, isLoaded]);

  // Pan to selected location
  useEffect(() => {
    if (!map || !selectedLocation || !isLoaded) return;

    map.panTo({ lat: selectedLocation.lat, lng: selectedLocation.lng });
    map.setZoom(15);

    // Find and highlight the selected marker
    const selectedMarker = markers.find(marker => 
      marker && marker.getTitle && marker.getTitle() === selectedLocation.name
    );
    
    if (selectedMarker && selectedMarker.setAnimation) {
      selectedMarker.setAnimation(window.google.maps.Animation.BOUNCE);
      setTimeout(() => {
        if (selectedMarker.setAnimation) {
          selectedMarker.setAnimation(null);
        }
      }, 2000);
    }
  }, [selectedLocation, map, markers, isLoaded]);

  return (
    <div className="map-wrapper">
      <div ref={mapRef} className="map-container">
        {!isLoaded && (
          <div className="map-loading">
            <div className="loader"></div>
            <p>Loading Google Maps...</p>
          </div>
        )}
      </div>
      
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
