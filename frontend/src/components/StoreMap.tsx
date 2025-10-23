import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { Store, MapCenter } from '@/types';
import { useCompanyLogo } from '@/hooks/useCompanyLogo';

interface StoreMapProps {
  center: MapCenter;
  stores: Store[];
  selectedStoreIds: Set<number>;
  onStoreSelect: (storeId: number) => void;
}

// --- Style Definitions ---
const markerHtmlStyles = `
  .map-logo-icon {
    background: transparent;
    border: none;
  }
  .map-logo-icon img {
    width: 35px;
    height: 35px;
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    transition: all 0.2s ease-in-out;
  }
  .desaturated img {
    filter: grayscale(100%);
    opacity: 0.6;
  }
  .map-logo-icon.selected img {
    border-color: #3b82f6; /* blue-500 */
    transform: scale(1.2);
  }
`;

// --- Helper Functions ---
const getZoomLevelForRadius = (radiusKm: number): number => {
  if (radiusKm <= 1) return 14;
  if (radiusKm <= 2) return 13;
  if (radiusKm <= 5) return 12;
  if (radiusKm <= 10) return 11;
  if (radiusKm <= 25) return 10;
  return 9;
};

// --- Child Components ---

const MapViewController: React.FC<{ center: MapCenter }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      const zoom = getZoomLevelForRadius(center.radius);
      map.setView([center.latitude, center.longitude], zoom);
    }
  }, [center, map]);
  return null;
};

const StoreMarker: React.FC<{ 
  store: Store; 
  isSelected: boolean; 
  onStoreSelect: (id: number) => void; 
  onMouseOver: (name: string) => void;
  onMouseOut: () => void;
}> = ({ store, isSelected, onStoreSelect, onMouseOver, onMouseOut }) => {
  const { objectUrl, isLoading } = useCompanyLogo(store.company_name);

  if (isLoading || !objectUrl) {
    return null; 
  }

  const icon = L.divIcon({
    html: `<img src="${objectUrl}" alt="${store.company_name} logo">`,
    className: `map-logo-icon ${isSelected ? 'selected' : 'desaturated'}`,
    iconSize: [35, 35],
    iconAnchor: [17, 35],
  });

  return (
    <Marker 
      key={store.id} 
      position={[store.latitude, store.longitude]}
      icon={icon}
      eventHandlers={{
        click: () => onStoreSelect(store.id),
        mouseover: () => onMouseOver(store.store_name),
        mouseout: onMouseOut,
      }}
    />
  );
};

// --- Main Map Component ---

const StoreMap: React.FC<StoreMapProps> = ({ center, stores, selectedStoreIds, onStoreSelect }) => {
    const [hoveredStoreName, setHoveredStoreName] = useState<string | null>(null);

    const displayCenter: [number, number] = center 
        ? [center.latitude, center.longitude] 
        : [-34.9285, 138.6007]; // Default center

    const displayZoom = center ? getZoomLevelForRadius(center.radius) : 13;

    return (
        <div style={{ height: '100%', width: '100%', position: 'relative' }}>
            {hoveredStoreName && (
              <div 
                className="absolute top-2 left-1/2 -translate-x-1/2 z-[1000] bg-background/90 p-2 rounded-md shadow-lg text-sm font-semibold"
              >
                {hoveredStoreName}
              </div>
            )}
            <style>{markerHtmlStyles}</style>
            <MapContainer center={displayCenter} zoom={displayZoom} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <MapViewController center={center} />
                {stores.map(store => (
                    <StoreMarker 
                        key={store.id}
                        store={store}
                        isSelected={selectedStoreIds.has(store.id)}
                        onStoreSelect={onStoreSelect}
                        onMouseOver={setHoveredStoreName}
                        onMouseOut={() => setHoveredStoreName(null)}
                    />
                ))}
            </MapContainer>
        </div>
    );
};

export default React.memo(StoreMap);