import React from 'react';
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";

// Import logos
import aldiLogo from '@/assets/ALDI_logo.svg';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

// Logo mapping
const companyLogos: { [key: string]: string } = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

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

const StoreList: React.FC<StoreListProps> = ({ stores, selectedStoreIds, onStoreSelect }) => {
  return (
    <div className="flex flex-col gap-2">
      {stores.map(store => {
        const isSelected = selectedStoreIds.has(store.id);
        const logo = companyLogos[store.company_name];

        return (
          <Card 
            key={store.id} 
            onClick={() => onStoreSelect(store.id)}
            className="cursor-pointer hover:bg-accent transition-colors"
          >
            <CardContent className="p-1.5 flex items-center gap-2">
              <Checkbox
                checked={isSelected}
                onCheckedChange={() => onStoreSelect(store.id)}
                aria-label={`Select ${store.store_name}`}
              />
              {logo && <img src={logo} alt={store.company_name} className="h-4 w-auto" />}
              <span className="font-medium text-sm truncate">{store.store_name}</span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default StoreList;
