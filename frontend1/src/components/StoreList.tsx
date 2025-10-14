import React from 'react';
import { Checkbox } from "@/components/ui/checkbox";
import { Card } from "@/components/ui/card";
import { Store } from '@/types'; // Import shared type

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
            // Overriding default card padding and applying flex layout directly
            className="p-2 flex flex-row items-center gap-3 cursor-pointer hover:bg-accent transition-colors"
          >
            <Checkbox
              checked={isSelected}
              onCheckedChange={() => onStoreSelect(store.id)}
              aria-label={`Select ${store.store_name}`}
            />
            {logo && <img src={logo} alt={store.company_name} className="h-5 w-auto" />}
            <span className="font-medium text-sm truncate">{store.store_name}</span>
          </Card>
        );
      })}
    </div>
  );
};

export default StoreList;
