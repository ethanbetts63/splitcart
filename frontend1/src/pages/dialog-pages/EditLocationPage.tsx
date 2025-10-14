import React, { useState, useEffect, useCallback } from 'react';
import StoreMap from '@/components/StoreMap';
import RadiusSlider from '@/components/RadiusSlider';
import CompanyFilter from '@/components/CompanyFilter';
import StoreList from '@/components/StoreList';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// Define the type for a single store based on the old component
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
} | null;

const EditLocationPage = () => {
  // State for user inputs
  const [postcode, setPostcode] = useState('');
  const [radius, setRadius] = useState(5);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  
  // State for data and loading
  const [location, setLocation] = useState<Location>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStoreIds, setSelectedStoreIds] = useState(new Set<number>());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- API Fetching Logic ---
  const handlePostcodeSearch = async () => {
    if (!postcode || !/^\d{4}$/.test(postcode)) {
      setError("Please enter a valid 4-digit postcode.");
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`/api/postcodes/search/?postcode=${postcode}`);
      if (!response.ok) throw new Error('Postcode not found.');
      const data = await response.json();
      setLocation({ latitude: data.latitude, longitude: data.longitude });
    } catch (err: any) {
      setError(err.message);
      setLocation(null);
    }
    // Loading state for the store fetch will be handled by the useEffect
  };

  useEffect(() => {
    if (!location) return;

    const fetchStores = async () => {
      setIsLoading(true);
      setError(null);
      const params = new URLSearchParams();
      params.append('latitude', location.latitude.toString());
      params.append('longitude', location.longitude.toString());
      params.append('radius', radius.toString());
      if (selectedCompanies.length > 0) {
        params.append('companies', selectedCompanies.join(','));
      }

      try {
        const response = await fetch(`/api/stores/nearby/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch stores.');
        const data = await response.json();
        setStores(data || []);
      } catch (err: any) {
        setError(err.message);
        setStores([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStores();
  }, [location, radius, selectedCompanies]);

  // --- Component Event Handlers ---
  const handleStoreSelect = (storeId: number) => {
    setSelectedStoreIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(storeId)) {
        newSet.delete(storeId);
      } else {
        newSet.add(storeId);
      }
      return newSet;
    });
  };

  return (
    <div className="flex h-full w-full">
      {/* Left Column for Controls and List */}
      <div className="w-1/3 border-r p-4 flex flex-col gap-4">
        <div className="grid gap-4">
          <h3 className="text-lg font-semibold">Controls</h3>
          <div className="grid gap-2">
            <label className="text-sm font-medium">Postcode</label>
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="4-digit postcode"
                value={postcode}
                onChange={(e) => setPostcode(e.target.value)}
                maxLength={4}
              />
              <Button onClick={handlePostcodeSearch} disabled={isLoading}>{isLoading ? '...' : 'Search'}</Button>
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
          </div>
          <RadiusSlider defaultValue={radius} onValueChange={setRadius} />
          <CompanyFilter onSelectionChange={setSelectedCompanies} />
        </div>
        <div className="flex flex-col min-h-0 flex-grow">
          <h3 className="text-lg font-semibold mb-2">Nearby Stores</h3>
          <div className="flex-grow overflow-y-auto pr-2">
            {isLoading && stores.length === 0 ? (
              <p>Loading stores...</p>
            ) : (
              <StoreList 
                stores={stores}
                selectedStoreIds={selectedStoreIds}
                onStoreSelect={handleStoreSelect}
              />
            )}
          </div>
        </div>
      </div>

      {/* Right Column for the Map */}
      <div className="flex-grow">
        <StoreMap 
          center={location}
          stores={stores}
          selectedStoreIds={selectedStoreIds}
          onStoreSelect={handleStoreSelect}
        />
      </div>
    </div>
  );
};

export default EditLocationPage;