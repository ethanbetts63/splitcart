
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Leaflet's default icon doesn't work well with React, so we need to fix it.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const StoreMap = () => {
    const [stores, setStores] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // TODO: Fetch stores from the API based on user's location
    useEffect(() => {
        // For now, we'll use some dummy data
        const dummyStores = [
            { id: 1, store_name: 'Dummy Store 1', latitude: -34.9285, longitude: 138.6007, company_name: 'Dummy Company' },
            { id: 2, store_name: 'Dummy Store 2', latitude: -34.93, longitude: 138.61, company_name: 'Dummy Company' },
        ];
        setStores(dummyStores);
        setLoading(false);
    }, []);

    if (loading) {
        return <div>Loading map...</div>;
    }

    if (error) {
        return <div>Error loading map: {error}</div>;
    }

    return (
        <MapContainer center={[-34.9285, 138.6007]} zoom={13} style={{ height: '500px', width: '100%' }}>
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {stores.map(store => (
                <Marker key={store.id} position={[store.latitude, store.longitude]}>
                    <Popup>
                        <b>{store.store_name}</b><br />
                        {store.company_name}
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
};

export default StoreMap;
