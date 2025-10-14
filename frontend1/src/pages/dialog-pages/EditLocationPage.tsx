import React, { useState, useCallback } from 'react';
import StoreMap from '@/components/StoreMap';
import RadiusSlider from '@/components/RadiusSlider';
import CompanyFilter from '@/components/CompanyFilter';
import StoreList from '@/components/StoreList';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useStoreSelection } from '@/context/StoreContext'; // Import the context hook

// Define the type for a single store
type Store = {
  id: number;
  store_name: string;
  company_name: string;
  latitude: number;
  longitude: number;
};

// The map center state now also includes the radius used for the search
type MapCenter = {
  latitude: number;
  longitude: number;
  radius: number;
} | null;

const EditLocationPage = () => {
  // --- Use global state for store selection ---
  const { selectedStoreIds, handleStoreSelect, setSelectedStoreIds } = useStoreSelection();

  // State for user inputs
  const [postcode, setPostcode] = useState('5000'); // Default to a valid postcode for demo
  const [radius, setRadius] = useState(5);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  
  // State for data and loading
  const [mapCenter, setMapCenter] = useState<MapCenter>({ latitude: -34.9285, longitude: 138.6007, radius: 5 }); // Default center
  const [stores, setStores] = useState<Store[] | null>(null); // Initialize to null to track initial state
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
      // Use the context function to select all stores by default
      setSelectedStoreIds(new Set((data || []).map(store => store.id))); 

      // Center map on the first result if available, bundling radius with it
      if (data && data.length > 0) {
        setMapCenter({ 
          latitude: data[0].latitude, 
          longitude: data[0].longitude, 
          radius: radius 
        });
      }

    } catch (err: any) {
      setError(err.message);
      setStores([]); // Set to empty array on error
    } finally {
      setIsLoading(false);
    }
  }, [postcode, radius, selectedCompanies, setSelectedStoreIds]);

  // Local handler for Enter key is still needed
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const renderStoreList = () => {
    if (stores === null) {
      return <p className="text-sm text-muted-foreground text-center">Please search for a postcode to see nearby stores.</p>;
    }
    if (isLoading) {
      return <p className="text-sm text-muted-foreground text-center">Loading stores...</p>;
    }
    if (stores.length === 0) {
        return <p className="text-sm text-muted-foreground text-center">No stores found for this search.</p>;
    }
    return (
        <StoreList 
            stores={stores}
            selectedStoreIds={selectedStoreIds}
            onStoreSelect={handleStoreSelect}
        />
    );
  }

  return (
    <div className="flex h-full w-full">
      {/* Left Column for Controls */}
      <div className="w-2/5 border-r p-4 flex flex-col gap-4">
        <h3 className="text-lg font-semibold">Controls</h3>
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
        <Button onClick={handleSearch} disabled={isLoading} className="w-full">{isLoading ? 'Searching...' : 'Search'}</Button>
      </div>

      {/* Right Column for Map and Store List */}
      <div className="flex-grow flex flex-col">
        {/* Top 1/2 for Map */}
        <div className="h-1/2">
            <StoreMap 
              center={mapCenter}
              stores={stores || []} // Pass empty array if stores is null
              selectedStoreIds={selectedStoreIds}
              onStoreSelect={handleStoreSelect}
            />
        </div>
        {/* Bottom 1/2 for Store List */}
        <div className="h-1/2 border-t flex flex-col">
            <div className="p-4 border-b">
                <h3 className="text-lg font-semibold">Selected Stores ({selectedStoreIds.size})</h3>
            </div>
            <div className="flex-grow overflow-y-auto p-4">
                {renderStoreList()}
            </div>
        </div>
      </div>
    </div>
  );
};

export default EditLocationPage;