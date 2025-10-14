import React from 'react';
import { Checkbox } from "@/components/ui/checkbox";
import { Card } from "@/components/ui/card";

// Define the type for a single store based on the old component
type Store = {
  id: number;
  store_name: string;
  company_name: string;
};

interface StoreListProps {
  stores: Store[];
  selectedStoreIds: Set<number>;
  onStoreSelect: (storeId: number) => void;
}

const StoreList: React.FC<StoreListProps> = ({ stores, selectedStoreIds, onStoreSelect }) => {
  return (
    <div className="flex flex-col gap-2 overflow-y-auto pr-2">
      {stores.map(store => {
        const isSelected = selectedStoreIds.has(store.id);
        return (
          <Card 
            key={store.id} 
            onClick={() => onStoreSelect(store.id)}
            className="p-3 flex items-center gap-4 cursor-pointer hover:bg-accent transition-colors"
          >
            <Checkbox
              checked={isSelected}
              onCheckedChange={() => onStoreSelect(store.id)}
              aria-label={`Select ${store.store_name}`}
            />
            <div className="flex flex-col">
              <span className="font-medium">{store.store_name}</span>
              <span className="text-sm text-muted-foreground">{store.company_name}</span>
            </div>
          </Card>
        );
      })}
    </div>
  );
};

export default StoreList;
