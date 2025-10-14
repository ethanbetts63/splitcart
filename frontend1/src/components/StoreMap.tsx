import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Store, MapCenter } from '@/types'; // Import shared types

// --- Asset Imports ---
import aldiLogo from '@/assets/ALDI_logo.svg';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

interface StoreMapProps {
  center: MapCenter;
  stores: Store[];
  selectedStoreIds: Set<number>;
  onStoreSelect: (storeId: number) => void;
}

// --- Icon & Style Definitions ---
const companyLogos: { [key: string]: string } = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

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

// --- Helper component to control map view ---
const MapViewController: React.FC<{ center: MapCenter }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      const zoom = getZoomLevelForRadius(center.radius);
      map.setView([center.latitude, center.longitude], zoom);
    }
  }, [center, map]); // Only runs when the center object changes
  return null;
};

const StoreMap: React.FC<StoreMapProps> = ({ center, stores, selectedStoreIds, onStoreSelect }) => {
    const displayCenter: [number, number] = center 
        ? [center.latitude, center.longitude] 
        : [-34.9285, 138.6007]; // Default center

    const displayZoom = center ? getZoomLevelForRadius(center.radius) : 13;

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <style>{markerHtmlStyles}</style>
            <MapContainer center={displayCenter} zoom={displayZoom} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <MapViewController center={center} />
                {stores.map(store => {
                    const isSelected = selectedStoreIds.has(store.id);
                    const iconUrl = companyLogos[store.company_name] || 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png'; // Fallback icon
                    
                    const icon = L.divIcon({
                        html: `<img src="${iconUrl}" alt="${store.company_name} logo">`,
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
                                click: () => {
                                    onStoreSelect(store.id);
                                },
                            }}
                        >
                            <Popup>
                                {store.store_name}
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
};

export default StoreMap;