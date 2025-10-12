
import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import '../css/StoreMap.css';
import L from 'leaflet';
import axios from 'axios';
import aldiLogo from '../assets/ALDI_logo.svg';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';
import CheckableStoreList from './CheckableStoreList';
import { useShoppingList } from '../context/ShoppingListContext';

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
    border: 3px solid var(--danger); /* Bootstrap's danger color */
    border-radius: 50%;
    box-shadow: 0 0 10px var(--danger);
  }
`;

const MapUpdater = ({ center, zoom }) => {
    const map = useMap();
    useEffect(() => {
        if (center) {
            map.setView(center, zoom);
        }
    }, [center, zoom, map]);
    return null;
}

const StoreMap = ({ onSelectionChange }) => {
    useEffect(() => {
        const styleElement = document.createElement('style');
        styleElement.innerHTML = selectedMarkerStyle;
        document.head.appendChild(styleElement);
        return () => {
            document.head.removeChild(styleElement);
        };
    }, []);

    const { userLocation, setUserLocation } = useShoppingList();
    const [stores, setStores] = useState([]);
    const [selectedStoreIds, setSelectedStoreIds] = useState(new Set());
    const [radius, setRadius] = useState(userLocation?.radius || 10);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [hasSearched, setHasSearched] = useState(false);

    const getZoomLevel = (radius) => {
        if (radius <= 2) return 14;
        if (radius <= 5) return 13;
        if (radius <= 10) return 12;
        if (radius <= 20) return 11;
        if (radius <= 50) return 10;
        return 9;
    };

    const fetchStores = useCallback(async () => {
        if (userLocation && userLocation.latitude && userLocation.longitude) {
            setLoading(true);
            try {
                const geoResponse = await axios.get('https://nominatim.openstreetmap.org/reverse', {
                    params: {
                        lat: userLocation.latitude,
                        lon: userLocation.longitude,
                        format: 'json',
                    }
                });
                const postcode = geoResponse.data.address.postcode;
                if (postcode) {
                    const response = await axios.get('/api/stores/nearby/', {
                        params: { postcode: postcode, radius: radius }
                    });
                    setStores(response.data);
                    setSelectedStoreIds(new Set(response.data.map(store => store.id)));
                } else {
                    setError('Could not determine postcode for the selected location.');
                }
            } catch (err) {
                setError('Could not fetch store data.');
            } finally {
                setLoading(false);
                setHasSearched(true);
            }
        }
    }, [userLocation, radius]);

    useEffect(() => {
        fetchStores();
    }, [fetchStores]);

    const MapClickHandler = () => {
        useMapEvents({
            click: async (e) => {
                const { lat, lng } = e.latlng;
                setStores([]);
                setHasSearched(false);
                setUserLocation({ latitude: lat, longitude: lng, radius });
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

    const mapCenter = userLocation ? [userLocation.latitude, userLocation.longitude] : [-25.36, 134.21];
    const mapZoom = userLocation ? getZoomLevel(radius) : 3.9;

    return (
        <div>
            <p style={{ color: 'var(--text-muted)', marginTop: '0' }}>
                Click on the map to set your location. 
                Check and uncheck specific stores below the map. 
                The more stores you select, the more saving potential you allow.
            </p>

            <div style={{ backgroundColor: 'white', color: 'black', padding: '1rem', borderRadius: '8px', border: '0.3px solid var(--colorp2)', marginBottom: '1rem' }}>
                <label>Search Radius: {radius} km</label>
                <input 
                    type="range" 
                    min="1" 
                    max="100" 
                    value={radius} 
                    onChange={(e) => setRadius(e.target.value)} 
                    className="radius-slider"
                />
            </div>

            <div style={{ position: 'relative', border: '0.3px solid black', borderRadius: '8px', overflow: 'hidden' }}>
              <MapContainer center={mapCenter} zoom={mapZoom} style={{ height: '400px', width: '100%' }}>
                  <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  <MapClickHandler />
                  <MapUpdater center={mapCenter} zoom={mapZoom} />
                  {userLocation && <Marker position={mapCenter} />} 
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
              <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 1000, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                <div style={{ backgroundColor: 'white', color: 'black', padding: '0.2rem 0.4rem', borderRadius: '8px', fontSize: '0.8rem', border: '0.3px solid var(--colorp2)' }}>
                  click and drag to move
                </div>
                <div style={{ backgroundColor: 'white', color: 'black', padding: '0.2rem 0.4rem', borderRadius: '8px', fontSize: '0.8rem', border: '0.3px solid var(--colorp2)' }}>
                  scroll or +/- to zoom
                </div>
                <div style={{ backgroundColor: 'white', color: 'black', padding: '0.2rem 0.4rem', borderRadius: '8px', fontSize: '0.8rem', border: '0.3px solid var(--colorp2)' }}>
                  click to select area
                </div>
              </div>
              {hasSearched && stores.length === 0 && (
                <div style={{
                  position: 'absolute',
                  bottom: '10px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  backgroundColor: 'var(--danger)',
                  color: 'white',
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  textAlign: 'center',
                  zIndex: 1000,
                }}>
                    No store data in this area
                </div>
              )}
            </div>

            <div style={{ marginTop: '-1rem' }}>
                <h5 style={{ marginBottom: '0.5rem', fontFamily: 'Vollkorn', fontStyle: 'italic', color: 'var(--primary)', fontSize: '1.5rem' }}>Selected Stores ↓</h5>
                {stores.length === 0 && (
                    <div style={{ backgroundColor: 'var(--colorp3)', padding: '0.5rem', borderRadius: '8px', fontSize: '1.3rem', marginBottom: '1rem' }}>
                        Click anywhere in the map to select stores
                    </div>
                )}
                <CheckableStoreList 
                    stores={stores} 
                    selectedStoreIds={selectedStoreIds} 
                    onStoreSelect={handleStoreSelect} 
                />
            </div>
        </div>
    );
};

export default StoreMap;
