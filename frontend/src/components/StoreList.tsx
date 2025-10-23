import React from 'react';
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { useCompanyLogo } from '@/hooks/useCompanyLogo';
import { Skeleton } from '@/components/ui/skeleton';

// Define the type for a single store
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

// Internal component to handle the logo loading state
const StoreLogo = ({ companyName }: { companyName: string }) => {
  const { objectUrl, isLoading, error } = useCompanyLogo(companyName);

  if (isLoading) {
    return <Skeleton className="h-4 w-10" />;
  }

  if (error || !objectUrl) {
    return <div className="h-4 w-10 flex items-center justify-center text-xs text-red-500">?</div>;
  }

  return <img src={objectUrl} alt={companyName} className="h-4 w-auto" />;
};

const StoreList: React.FC<StoreListProps> = ({ stores, selectedStoreIds, onStoreSelect }) => {
  return (
    <div className="flex flex-col gap-2">
      {stores.map(store => {
        const isSelected = selectedStoreIds.has(store.id);

        return (
          <Card 
            key={store.id} 
            onClick={() => onStoreSelect(store.id)}
            className="cursor-pointer hover:bg-accent transition-colors py-1"
          >
            <CardContent className="px-1 py-0.5 flex items-center gap-2">
              <div onClick={(e) => e.stopPropagation()}>
                <Checkbox
                  checked={isSelected}
                  onCheckedChange={() => onStoreSelect(store.id)}
                  aria-label={`Select ${store.store_name}`}
                />
              </div>
              <StoreLogo companyName={store.company_name} />
              <span className="font-medium text-sm truncate">{store.store_name}</span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default React.memo(StoreList);
