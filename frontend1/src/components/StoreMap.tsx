import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Define the types for props
type Store = {
  id: number;
  store_name: string;
  company_name: string;
  latitude: number;
  longitude: number;
};

type Location = {
  latitude: number;
  longitude: number;
};

interface StoreMapProps {
  center: Location | null;
  stores: Store[];
  selectedStoreIds: Set<number>;
  onStoreSelect: (storeId: number) => void;
}

// --- Icon Definitions ---
// Fix for default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Custom icon for selected markers
const selectedIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// --- Helper component to control map view ---
const MapViewController: React.FC<{ center: Location | null }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView([center.latitude, center.longitude], 13); // Zoom to level 13 on new center
    }
  }, [center, map]);
  return null;
};

const StoreMap: React.FC<StoreMapProps> = ({ center, stores, selectedStoreIds, onStoreSelect }) => {
    const displayCenter: [number, number] = center 
        ? [center.latitude, center.longitude] 
        : [-34.9285, 138.6007]; // Default center

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <MapContainer center={displayCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <MapViewController center={center} />
                {stores.map(store => (
                    <Marker 
                        key={store.id} 
                        position={[store.latitude, store.longitude]}
                        icon={selectedStoreIds.has(store.id) ? selectedIcon : new L.Icon.Default()}
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
                ))}
            </MapContainer>
        </div>
    );
};

export default StoreMap;