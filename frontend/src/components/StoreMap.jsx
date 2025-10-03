
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import axios from 'axios';
import { Form } from 'react-bootstrap';

import aldiLogo from '../assets/ALDI_logo.svg';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';
import CheckableStoreList from './CheckableStoreList';

const companyLogos = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

const getStoreIcon = (companyName, isSelected) => {
    const logoUrl = companyLogos[companyName];
    const className = `leaflet-marker-icon ${isSelected ? 'marker-selected' : ''}`;

    if (logoUrl) {
        return new L.Icon({
            iconUrl: logoUrl,
            iconSize: [40, 40],
            className: className,
        });
    }

    // Fallback to default icon
    return new L.Icon({
        iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41],
        className: className,
    });
};

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
    const [userLocation, setUserLocation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const MapClickHandler = () => {
        useMapEvents({
            dblclick: async (e) => {
                const { lat, lng } = e.latlng;
                setUserLocation({ lat, lng });
                setLoading(true);
                try {
                    // Reverse geocode to get postcode
                    const geoResponse = await axios.get('https://nominatim.openstreetmap.org/reverse', {
                        params: {
                            lat: lat,
                            lon: lng,
                            format: 'json',
                        }
                    });
                    const postcode = geoResponse.data.address.postcode;
                    if (postcode) {
                        // Fetch stores with the new postcode
                        const response = await axios.get('/api/stores/nearby/', {
                            params: { postcode: postcode, radius: radius }
                        });
                        setStores(response.data);
                    } else {
                        setError('Could not determine postcode for the selected location.');
                    }
                } catch (err) {
                    setError('Could not fetch store data.');
                } finally {
                    setLoading(false);
                }
            },
        });
        return null;
    };

    const handleStoreSelect = (storeId) => {
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
            {error && <div>Error: {error}</div>}

            <MapContainer center={[-25.36, 134.21]} zoom={4} style={{ height: '400px', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <MapClickHandler />
                {userLocation && <Marker position={userLocation} />} 
                {stores.map(store => (
                    <Marker 
                        key={store.id} 
                        position={[store.latitude, store.longitude]}
                        icon={getStoreIcon(store.company_name, selectedStoreIds.has(store.id))}
                        eventHandlers={{
                            click: () => handleStoreSelect(store.id),
                        }}
                    >
                        <Popup>
                            <b>{store.store_name}</b><br />
                            {store.company_name}
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>

            <div className="mt-4">
                <Row>
                    <Col md={6}>
                        <h5>Nearby Stores</h5>
                        <CheckableStoreList 
                            stores={stores} 
                            selectedStoreIds={selectedStoreIds} 
                            onStoreSelect={handleStoreSelect} 
                        />
                    </Col>
                    <Col md={6}>
                        <h5>Selected Stores</h5>
                        <CheckableStoreList 
                            stores={stores.filter(store => selectedStoreIds.has(store.id))} 
                            selectedStoreIds={selectedStoreIds} 
                            onStoreSelect={handleStoreSelect} 
                        />
                    </Col>
                </Row>
            </div>
        </div>
    );
};

export default StoreMap;
