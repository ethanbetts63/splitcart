
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import axios from 'axios';
import { Form } from 'react-bootstrap';

const selectedMarkerStyle = `
  .marker-selected img {
    border: 3px solid #dc3545; /* Bootstrap's danger color */
    border-radius: 50%;
    box-shadow: 0 0 10px #dc3545;
  }
`;

const StoreMap = ({ onSelectionChange }) => {
    // Inject the style into the document head
    useEffect(() => {
        const styleElement = document.createElement('style');
        styleElement.innerHTML = selectedMarkerStyle;
        document.head.appendChild(styleElement);
        return () => {
            document.head.removeChild(styleElement);
        };
    }, []);

    const [stores, setStores] = useState([]);
    const [selectedStoreIds, setSelectedStoreIds] = useState(new Set());
    const [radius, setRadius] = useState(5);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStores = async () => {
            setLoading(true);
            try {
                const response = await axios.get('/api/stores/nearby/', {
                    params: { postcode: 5000, radius: radius }
                });
                setStores(response.data);
            } catch (err) {
                setError('Could not fetch store data.');
            } finally {
                setLoading(false);
            }
        };

        fetchStores();
    }, [radius]);

    const handleMarkerClick = (storeId) => {
        const newSelectedIds = new Set(selectedStoreIds);
        if (newSelectedIds.has(storeId)) {
            newSelectedIds.delete(storeId);
        } else {
            newSelectedIds.add(storeId);
        }
        setSelectedStoreIds(newSelectedIds);
        if (onSelectionChange) {
            onSelectionChange(Array.from(newSelectedIds));
        }
    };

    return (
        <div>
            <Form.Group controlId="radiusSlider" className="mb-3">
                <Form.Label>Search Radius: {radius} km</Form.Label>
                <Form.Control 
                    type="range" 
                    min="1" 
                    max="100" 
                    value={radius} 
                    onChange={(e) => setRadius(e.target.value)} 
                />
            </Form.Group>

            {loading && <div>Loading map...</div>}
            {error && <div>Error loading map: {error}</div>}

            <MapContainer center={[-34.9285, 138.6007]} zoom={13} style={{ height: 'calc(100vh - 150px)', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {stores.map(store => (
                    <Marker 
                        key={store.id} 
                        position={[store.latitude, store.longitude]}
                        icon={getStoreIcon(store.company_name, selectedStoreIds.has(store.id))}
                        eventHandlers={{
                            click: () => handleMarkerClick(store.id),
                        }}
                    >
                        <Popup>
                            <b>{store.store_name}</b><br />
                            {store.company_name}
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
};

export default StoreMap;
