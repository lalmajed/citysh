import React, { useEffect, useRef, useState } from 'react';
import './RiyadhMap.css';

const typeColors = {
  landmark: '#e74c3c',
  mall: '#3498db',
  road: '#f39c12',
  district: '#27ae60',
  custom: '#9b59b6'
};

function RiyadhMap({ locations, selectedLocation, onLocationClick }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const infoWindowRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load Google Maps and initialize
  useEffect(() => {
    let checkInterval;

    const initializeMap = () => {
      if (!mapContainerRef.current || mapInstanceRef.current) return;

      try {
        mapInstanceRef.current = new window.google.maps.Map(mapContainerRef.current, {
          center: { lat: 24.7136, lng: 46.6753 },
          zoom: 12,
          mapTypeControl: true,
          streetViewControl: true,
          fullscreenControl: true
        });

        infoWindowRef.current = new window.google.maps.InfoWindow();
        setIsLoaded(true);
      } catch (error) {
        console.error('Error initializing map:', error);
      }
    };

    // Set global initMap
    window.initMap = initializeMap;

    // Check if Google Maps is already loaded
    if (window.google?.maps?.Map) {
      initializeMap();
    } else {
      // Load script if not already loading
      if (!document.querySelector('script[src*="Keyless-Google-Maps-API"]')) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/gh/somanchiu/Keyless-Google-Maps-API@v7.1/mapsJavaScriptAPI.js';
        script.async = true;
        document.head.appendChild(script);
      }

      // Poll for Google Maps to be ready
      checkInterval = setInterval(() => {
        if (window.google?.maps?.Map) {
          clearInterval(checkInterval);
          initializeMap();
        }
      }, 200);
    }

    return () => {
      if (checkInterval) clearInterval(checkInterval);
    };
  }, []);

  // Update markers when locations change
  useEffect(() => {
    if (!mapInstanceRef.current || !isLoaded) return;

    // Clear old markers
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    // Add new markers
    locations.forEach(location => {
      const marker = new window.google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: mapInstanceRef.current,
        title: location.name,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          fillColor: typeColors[location.type] || typeColors.custom,
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
          scale: 10
        }
      });

      marker.addListener('click', () => {
        if (infoWindowRef.current) {
          infoWindowRef.current.setContent(`
            <div style="padding: 10px; min-width: 150px;">
              <h3 style="margin: 0 0 8px 0; color: #2c3e50;">${location.name}</h3>
              <p style="margin: 4px 0; color: #7f8c8d;"><strong>Type:</strong> ${location.type}</p>
              <p style="margin: 4px 0; color: #7f8c8d;"><strong>Lat:</strong> ${location.lat.toFixed(4)}</p>
              <p style="margin: 4px 0; color: #7f8c8d;"><strong>Lng:</strong> ${location.lng.toFixed(4)}</p>
            </div>
          `);
          infoWindowRef.current.open(mapInstanceRef.current, marker);
        }
        if (onLocationClick) onLocationClick(location);
      });

      markersRef.current.push(marker);
    });
  }, [locations, isLoaded, onLocationClick]);

  // Pan to selected location
  useEffect(() => {
    if (!mapInstanceRef.current || !selectedLocation || !isLoaded) return;

    mapInstanceRef.current.panTo({ 
      lat: selectedLocation.lat, 
      lng: selectedLocation.lng 
    });
    mapInstanceRef.current.setZoom(15);

    // Bounce the selected marker
    const selectedMarker = markersRef.current.find(
      marker => marker.getTitle() === selectedLocation.name
    );
    if (selectedMarker) {
      selectedMarker.setAnimation(window.google.maps.Animation.BOUNCE);
      setTimeout(() => selectedMarker.setAnimation(null), 2000);
    }
  }, [selectedLocation, isLoaded]);

  return (
    <div className="map-wrapper">
      {!isLoaded && (
        <div className="map-loading">
          <div className="loader"></div>
          <p>Loading Google Maps...</p>
        </div>
      )}
      <div 
        ref={mapContainerRef} 
        className="map-container"
        style={{ visibility: isLoaded ? 'visible' : 'hidden' }}
      />
      <div className="map-legend">
        <h4>Legend</h4>
        {Object.entries(typeColors).map(([type, color]) => (
          <div key={type} className="legend-item">
            <span className="legend-color" style={{ backgroundColor: color }}></span>
            <span className="legend-label">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RiyadhMap;
