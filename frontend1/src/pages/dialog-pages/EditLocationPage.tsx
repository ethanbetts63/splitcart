import React, { useState } from 'react';
import StoreMap from '@/components/StoreMap';
import RadiusSlider from '@/components/RadiusSlider';
import CompanyFilter from '@/components/CompanyFilter';
import StoreList from '@/components/StoreList';

// Mock Data for layout purposes
const mockStores = [
  { id: 1, store_name: 'Coles Central', company_name: 'Coles' },
  { id: 2, store_name: 'Woolworths Metro', company_name: 'Woolworths' },
  { id: 3, store_name: 'Aldi City', company_name: 'Aldi' },
  { id: 4, store_name: 'IGA Express', company_name: 'IGA' },
  { id: 5, store_name: 'Woolworths Suburb', company_name: 'Woolworths' },
];

const EditLocationPage = () => {
  const [stores, setStores] = useState(mockStores);
  const [selectedStoreIds, setSelectedStoreIds] = useState(new Set([2, 5]));

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
          <RadiusSlider />
          <CompanyFilter />
        </div>
        <div className="flex flex-col min-h-0">
          <h3 className="text-lg font-semibold mb-2">Nearby Stores</h3>
          <div className="flex-grow overflow-y-auto">
            <StoreList 
              stores={stores}
              selectedStoreIds={selectedStoreIds}
              onStoreSelect={handleStoreSelect}
            />
          </div>
        </div>
      </div>

      {/* Right Column for the Map */}
      <div className="flex-grow">
        <StoreMap />
      </div>
    </div>
  );
};

export default EditLocationPage;
