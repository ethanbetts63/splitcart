import React, { useState, useCallback, useEffect } from 'react';
import StoreMap from '../../components/StoreMap';
import RadiusSlider from '../../components/RadiusSlider';
import CompanyFilter from '../../components/CompanyFilter';
import StoreList from '../../components/StoreList';
import MultiplePostcodeInput from '../../components/MultiplePostcodeInput';
import { Button } from '../../components/ui/button';
import { useAuth } from '../../context/AuthContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Label } from "../../components/ui/label";
import { Input } from "../../components/ui/input";
import { PlusCircle, Save, Trash2, Pencil } from 'lucide-react';

import { useStoreSearch } from '../../context/StoreSearchContext';
import { useStoreList } from '../../context/StoreListContext';
import type { EditLocationPageProps } from '../../types/EditLocationPageProps';

const EditLocationPage: React.FC<EditLocationPageProps> = ({ localSelectedStoreIds, setLocalSelectedStoreIds, onOpenChange, setHasSearchOccurred }) => {
  const { isAuthenticated } = useAuth();
  const {
    postcode, setPostcode,
    radius, setRadius,
    selectedCompanies, setSelectedCompanies,
    mapBounds,
    stores,
    isLoading,
    error,
    handleSearch,
  } = useStoreSearch();

  const {
    // selectedStoreIds and handleStoreSelect are now managed by the parent
    currentStoreListId,
    currentStoreListName, setCurrentStoreListName,
    userStoreLists,
    storeListLoading,
    loadStoreList, saveStoreList, createNewStoreList, deleteStoreList,
  } = useStoreList();

  const [isEditingListName, setIsEditingListName] = useState(false);

  useEffect(() => {
    console.log('EditLocationPage - Store List ID:', currentStoreListId);
    console.log('EditLocationPage - Store List Name:', currentStoreListName);
  }, [currentStoreListId, currentStoreListName]);



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

  const onSearch = async () => {
    const fetchedStores = await handleSearch();
    if (fetchedStores) {
        // When a new search is performed, update the local state directly
        setLocalSelectedStoreIds(new Set(fetchedStores.map(store => store.id))); 
        setHasSearchOccurred(true); // Set the flag here
    }
  }





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
      <div className="w-3/7 border-r p-4 flex flex-col gap-3">
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
            <label className="text-sm font-medium flex items-center justify-between">
                <span>Postcode</span>
                <span className="text-xs text-muted-foreground">e.g. Home, Work, School</span>
            </label>
            <MultiplePostcodeInput
                value={postcode}
                onChange={setPostcode}
            />
            {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
        <RadiusSlider defaultValue={radius} onValueChange={setRadius} />
        <CompanyFilter 
          selectedCompanies={selectedCompanies}
          onSelectionChange={setSelectedCompanies} 
        />
        <Button onClick={onSearch} disabled={isLoading} className="w-full">{isLoading ? 'Searching...' : 'Search'}</Button>
        {localSelectedStoreIds.size > 0 && (
          <Button onClick={() => onOpenChange(false)} className="w-full bg-green-500 hover:bg-green-600">Done</Button>
        )}
      </div>

      {/* Right Column for Map and Store List */}
      <div className="flex-grow flex flex-col">
        {/* Top 1/2 for Map */}
        <div className="h-1/2">
            <StoreMap 
              bounds={mapBounds}
              stores={stores || []} // Pass empty array if stores is null
              selectedStoreIds={localSelectedStoreIds} // Use local state
              onStoreSelect={handleLocalStoreSelect} // Use local handler
            />
        </div>
        {/* Bottom 1/2 for Store List */}
        <div className="h-1/2 border-t flex flex-col">
            <div className="px-2 pb-2 pt-1 border-b">
                <h3 className="text-lg font-semibold">Selected Stores ({localSelectedStoreIds.size})</h3>
                <p className="text-sm text-muted-foreground">Click stores below or in the map to enable/disable.</p>
            </div>
            <div className="flex-grow overflow-y-auto p-2">
                {renderStoreList()}
            </div>
        </div>
      </div>
    </div>
  );
};

export default EditLocationPage;

