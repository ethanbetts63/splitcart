import React from 'react';
import { AspectRatio } from '../components/ui/aspect-ratio';
import confusedShopper from "../assets/confused_shopper.webp"; 
import confusedShopper320 from "../assets/confused_shopper-320w.webp"; 
import confusedShopper640 from "../assets/confused_shopper-640w.webp"; 
import confusedShopper768 from "../assets/confused_shopper-768w.webp"; 
import confusedShopper1024 from "../assets/confused_shopper-1024w.webp"; 
import confusedShopper1280 from "../assets/confused_shopper-1280w.webp"; 
import { useDocumentHead } from '@/hooks/useDocumentHead';
import { useStoreList } from '../context/StoreListContext';
import { ProductCarousel } from "../components/ProductCarousel";

const BargainsPage: React.FC = () => {
    useDocumentHead(
        "SplitCart: Australia's Best Grocery Bargains",
        "Find the best grocery bargains in Australia. SplitCart compares prices across Coles, Woolworths, Aldi, and IGA to find you the biggest discounts."
    );

  const hero_title = "Australia's Best Grocery Bargains";
  const introduction_paragraph = "We've scoured the shelves to find the products with the biggest discounts. Here are the top grocery bargains available right now from your selected stores. Happy hunting!";
  const imageUrl = confusedShopper;

  const DEFAULT_STORE_IDS = [
    515, 5123, 518, 523, 272, 276, 2197, 2198, 2199, 536, 5142, 547, 2218, 2219,
    2224, 5074, 5080, 5082, 5083, 5094, 5096, 5100, 498, 505, 254,
  ];
  const { selectedStoreIds } = useStoreList();
  const isDefaultStores = selectedStoreIds.size === 0;
  const storeIdsArray = React.useMemo(() =>
    isDefaultStores ? DEFAULT_STORE_IDS : Array.from(selectedStoreIds),
    [selectedStoreIds, isDefaultStores]
  );
  
  const companies = [
      { name: 'Coles', id: 1 },
      { name: 'Woolworths', id: 2 },
      { name: 'Aldi', id: 3 },
      { name: 'Iga', id: 4 }
  ]

  return (
    <div>
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img 
                src={imageUrl} 
                srcSet={`${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`}
                sizes="(min-width: 1024px) 50vw, 100vw"
                alt={hero_title}
                className="rounded-md object-cover w-full h-full"
                fetchPriority="high" />
            </AspectRatio>
          </div>
          <div className="text-left">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              {hero_title}
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              {introduction_paragraph}
            </p>
          </div>
        </div>
      </div>
      <div className="container mx-auto px-4 py-8">
            <div className="flex flex-col gap-8">
            {companies.map(company => (
                <ProductCarousel
                    key={company.id}
                    title={`${company.name} Bargains`}
                    sourceUrl={`/api/products/bargain-carousel/?company_id=${company.id}`}
                    storeIds={storeIdsArray}
                    isDefaultStores={isDefaultStores}
                />
            ))}
            </div>
      </div>
    </div>
  );
};

export default BargainsPage;

