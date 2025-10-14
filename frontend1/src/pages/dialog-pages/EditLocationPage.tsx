import React, { useState, useCallback } from 'react';
import StoreMap from '@/components/StoreMap';
import RadiusSlider from '@/components/RadiusSlider';
import CompanyFilter from '@/components/CompanyFilter';
import StoreList from '@/components/StoreList';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// Define the type for a single store
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
  const [postcode, setPostcode] = useState('5000'); // Default to a valid postcode for demo
  const [radius, setRadius] = useState(5);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  
  // State for data and loading
  const [mapCenter, setMapCenter] = useState<Location>({ latitude: -34.9285, longitude: 138.6007 }); // Default center
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStoreIds, setSelectedStoreIds] = useState(new Set<number>());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- API Fetching Logic ---
  const handleSearch = useCallback(async () => {
    if (!postcode || !/^\d{4}$/.test(postcode)) {
      setError("Please enter a valid 4-digit postcode.");
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setStores([]); // Clear previous results

    const params = new URLSearchParams();
    params.append('postcode', postcode);
    params.append('radius', radius.toString());
    if (selectedCompanies.length > 0) {
      params.append('companies', selectedCompanies.join(','));
    }

    try {
      const response = await fetch(`/api/stores/nearby/?${params.toString()}`);
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to fetch stores.');
      }
      const data: Store[] = await response.json();
      setStores(data || []);

      // Center map on the first result if available
      if (data && data.length > 0) {
        setMapCenter({ latitude: data[0].latitude, longitude: data[0].longitude });
      }

    } catch (err: any) {
      setError(err.message);
      setStores([]);
    } finally {
      setIsLoading(false);
    }
  }, [postcode, radius, selectedCompanies]);

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

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="flex h-full w-full">
      {/* Left Column for Store List */}
      <div className="w-1/3 border-r flex flex-col">
        <div className="p-4 border-b">
            <h3 className="text-lg font-semibold">Nearby Stores ({stores.length})</h3>
        </div>
        <div className="flex-grow overflow-y-auto p-4">
            {isLoading ? (
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

      {/* Right Column for Map and Controls */}
      <div className="flex-grow flex flex-col">
        {/* Top 1/2 for Map */}
        <div className="h-1/2">
            <StoreMap 
              center={mapCenter}
              stores={stores}
              selectedStoreIds={selectedStoreIds}
              onStoreSelect={handleStoreSelect}
            />
        </div>
        {/* Bottom 1/2 for Controls */}
        <div className="h-1/2 border-t p-4 grid gap-4 overflow-y-auto">

            <div className="grid gap-2">
                <label className="text-sm font-medium">Postcode</label>
                <div className="flex gap-2">
                <Input
                    type="text"
                    placeholder="4-digit postcode"
                    value={postcode}
                    onChange={(e) => setPostcode(e.target.value)}
                    onKeyDown={handleKeyDown}
                    maxLength={4}
                />
                <Button onClick={handleSearch} disabled={isLoading}>{isLoading ? '...' : 'Search'}</Button>
                </div>
                {error && <p className="text-sm text-red-500">{error}</p>}
            </div>
            <RadiusSlider defaultValue={radius} onValueChange={setRadius} />
            <CompanyFilter onSelectionChange={setSelectedCompanies} />
        </div>
      </div>
    </div>
  );
};

export default EditLocationPage;