import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { Store } from '@/types';
import { useCompanyLogo } from '@/hooks/useCompanyLogo';

type MapBounds = [[number, number], [number, number]] | null;

interface StoreMapProps {
  bounds: MapBounds;
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

// --- Child Components ---

const MapViewController: React.FC<{ bounds: MapBounds }> = ({ bounds }) => {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
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

const StoreMap: React.FC<StoreMapProps> = ({ bounds, stores, selectedStoreIds, onStoreSelect }) => {
    const [hoveredStoreName, setHoveredStoreName] = useState<string | null>(null);

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
            <MapContainer center={[-27, 133]} zoom={4} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <MapViewController bounds={bounds} />
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