import React, { useState, useCallback, useEffect } from 'react';
import StoreMap from '@/components/StoreMap';
import RadiusSlider from '@/components/RadiusSlider';
import CompanyFilter from '@/components/CompanyFilter';
import StoreList from '@/components/StoreList';
import MultiplePostcodeInput from '@/components/MultiplePostcodeInput';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { PlusCircle, Save, Trash2, Star, Pencil } from 'lucide-react'; // Icons for actions

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

import { useStoreSearch } from '@/context/StoreSearchContext';
import { useStoreList } from '@/context/StoreListContext';

interface EditLocationPageProps {
  localSelectedStoreIds: Set<number>;
  setLocalSelectedStoreIds: React.Dispatch<React.SetStateAction<Set<number>>>;
}

const EditLocationPage: React.FC<EditLocationPageProps> = ({ localSelectedStoreIds, setLocalSelectedStoreIds }) => {
  const { isAuthenticated, token, anonymousId } = useAuth();
  const {
    postcode, setPostcode,
    radius, setRadius,
    selectedCompanies, setSelectedCompanies,
    mapCenter, setMapCenter,
    stores, setStores
  } = useStoreSearch();

  const {
    // selectedStoreIds and handleStoreSelect are now managed by the parent
    setSelectedStoreIds, // Still needed for the search handler
    currentStoreListId, setCurrentStoreListId,
    currentStoreListName, setCurrentStoreListName,
    userStoreLists, setUserStoreLists,
    storeListLoading, setStoreListLoading,
    storeListError, setStoreListError,
    loadStoreList, saveStoreList, createNewStoreList, deleteStoreList, fetchActiveStoreList
  } = useStoreList();

  // State for loading and error, which is local to this page
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditingListName, setIsEditingListName] = useState(false);

  useEffect(() => {
    console.log('EditLocationPage - Store List ID:', currentStoreListId);
    console.log('EditLocationPage - Store List Name:', currentStoreListName);
  }, [currentStoreListId, currentStoreListName]);

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchActiveStoreList();
    } else if (!isAuthenticated && anonymousId) { // Fetch for anonymous users too
      fetchActiveStoreList();
    }
  }, [isAuthenticated, token, anonymousId, fetchActiveStoreList]);

  const handleLocalStoreSelect = useCallback((storeId: number) => {
    setLocalSelectedStoreIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(storeId)) {
        newSet.delete(storeId);
      } else {
        newSet.add(storeId);
      }
      return newSet;
    });
  }, [setLocalSelectedStoreIds]);

  // --- API Fetching Logic ---
  const handleSearch = useCallback(async () => {
    if (!postcode || postcode.split(',').some(p => !/^\d{4}$/.test(p.trim()))) {
      setError("Please enter valid 4-digit postcodes.");
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
      // When a new search is performed, update the local state directly
      setLocalSelectedStoreIds(new Set((data || []).map(store => store.id))); 

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
  }, [postcode, radius, selectedCompanies, setStores, setLocalSelectedStoreIds, setMapCenter]);



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
            selectedStoreIds={localSelectedStoreIds} // Use local state
            onStoreSelect={handleLocalStoreSelect} // Use local handler
        />
    );
  }

  return (
    <div className="flex h-full w-full">
      {/* Left Column for Controls */}
      <div className="w-3/7 border-r p-4 flex flex-col gap-4">
        <h3 className="text-lg font-semibold">Controls</h3>
        {isAuthenticated && (
            <div className="flex flex-col gap-2">
                <Label>Saved Store Lists</Label>
                <div className="flex items-center gap-2">
                    {isEditingListName ? (
                        <Input
                            id="store-list-name-edit"
                            type="text"
                            value={currentStoreListName}
                            onChange={(e) => setCurrentStoreListName(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    saveStoreList(currentStoreListName, Array.from(localSelectedStoreIds));
                                    setIsEditingListName(false);
                                    e.currentTarget.blur();
                                }
                            }}
                            disabled={storeListLoading}
                            className="flex-grow"
                        />
                    ) : (
                        <Select
                            value={currentStoreListId ?? ''}
                            onValueChange={(value) => {
                                if (value === "new") {
                                    createNewStoreList(Array.from(localSelectedStoreIds));
                                } else if (value) {
                                    loadStoreList(value);
                                }
                            }}
                        >
                            <SelectTrigger className="flex-grow">
                                <SelectValue>
                                    {currentStoreListName}
                                </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="new">
                                    <div className="flex items-center gap-2">
                                        <PlusCircle className="h-4 w-4" /> Create New List
                                    </div>
                                </SelectItem>
                                {userStoreLists.map((list) => (
                                    <SelectItem key={list.id} value={list.id}>
                                        {list.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    )}
                    <Button 
                        variant="outline" 
                        size="icon"
                        onClick={() => {
                            if (isEditingListName) {
                                saveStoreList(currentStoreListName, Array.from(localSelectedStoreIds));
                            }
                            setIsEditingListName(!isEditingListName);
                        }}
                        disabled={storeListLoading || !currentStoreListId}
                        className={isEditingListName ? "bg-green-500 text-white hover:bg-green-600" : ""}
                    >
                        {isEditingListName ? <Save className="h-4 w-4" /> : <Pencil className="h-4 w-4" />}
                    </Button>
                    <Button 
                        variant="destructive" 
                        size="icon"
                        onClick={() => currentStoreListId && deleteStoreList(currentStoreListId)}
                        disabled={storeListLoading || !currentStoreListId || isEditingListName}
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        )}
        <div className="grid gap-2">
            <label className="text-sm font-medium">Postcode</label>
            <MultiplePostcodeInput
                value={postcode}
                onChange={setPostcode}
            />
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
              selectedStoreIds={localSelectedStoreIds} // Use local state
              onStoreSelect={handleLocalStoreSelect} // Use local handler
            />
        </div>
        {/* Bottom 1/2 for Store List */}
        <div className="h-1/2 border-t flex flex-col">
            <div className="p-4 border-b">
                <h3 className="text-lg font-semibold">Selected Stores ({localSelectedStoreIds.size})</h3>
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
