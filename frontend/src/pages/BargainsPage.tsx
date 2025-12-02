import React from 'react';
import { AspectRatio } from '../components/ui/aspect-ratio';
import bargains from "../assets/bargains.webp"; 
import bargains320 from "../assets/bargains-320w.webp"; 
import bargains640 from "../assets/bargains-640w.webp"; 
import bargains768 from "../assets/bargains-768w.webp"; 
import bargains1024 from "../assets/bargains-1024w.webp"; 
import bargains1280 from "../assets/bargains-1280w.webp"; 
import { useDocumentHead } from '@/hooks/useDocumentHead';
import { useStoreList } from '../context/StoreListContext';
import { ProductCarousel } from "../components/ProductCarousel";
import { FAQ } from "../components/FAQ";
import { useApiQuery } from '../hooks/useApiQuery';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import type { PriceComparison } from '../types';
import PriceComparisonChart from '../components/PriceComparisonChart';
import LoadingSpinner from '../components/LoadingSpinner';

import snackLineup from "../assets/snack_lineup.webp";
import snackLineup320 from "../assets/snack_lineup-320w.webp"; 
import snackLineup640 from "../assets/snack_lineup-640w.webp"; 
import snackLineup768 from "../assets/snack_lineup-768w.webp"; 
import snackLineup1024 from "../assets/snack_lineup-1024w.webp"; 
import snackLineup1280 from "../assets/snack_lineup-1280w.webp";

const BargainsPage: React.FC = () => {
    useDocumentHead(
        "SplitCart: Australia's Best Grocery Bargains",
        "Find the best grocery bargains in Australia. SplitCart compares prices across Coles, Woolworths, Aldi, and IGA to find you the biggest discounts."
    );

  const hero_title = "Australia's Best Grocery Bargains";
  const introduction_paragraph = "Forget the flashy ‘specials’ — these are the real bargains hiding in plain sight. We’ve compared prices across supermarkets to show you who actually sells each item for less.";
  const imageUrl = bargains;

  const DEFAULT_ANCHOR_IDS = [105, 458, 549, 504, 562, 4186];
  
  const { selectedStoreIds, anchorStoreMap } = useStoreList();
  const isDefaultStores = selectedStoreIds.size === 0;

  const anchorStoreIdsArray = React.useMemo(() => {
    if (isDefaultStores) {
      return DEFAULT_ANCHOR_IDS;
    }
    const anchorIds = new Set<number>();
    for (const storeId of selectedStoreIds) {
      const anchorId = anchorStoreMap[storeId];
      if (anchorId) {
        anchorIds.add(anchorId);
      }
    }
    // Fallback to default if the mapping results in an empty list
    return anchorIds.size > 0 ? Array.from(anchorIds) : DEFAULT_ANCHOR_IDS;
  }, [selectedStoreIds, anchorStoreMap, isDefaultStores]);
  
  const companies = [
      { name: 'Coles', id: 1 },
      { name: 'Woolworths', id: 2 },
      { name: 'Aldi', id: 3 },
      { name: 'Iga', id: 4 }
  ];

  const {
    data: bargainStats,
    isLoading: isLoadingStats,
    isError: isErrorStats,
  } = useApiQuery<PriceComparison[]>(
    ['bargainStats'],
    '/api/stats/bargains/',
  );

  return (
    <div>
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img 
                src={imageUrl} 
                srcSet={`${bargains320} 320w, ${bargains640} 640w, ${bargains768} 768w, ${bargains1024} 1024w, ${bargains1280} 1280w`}
                sizes="(min-width: 1024px) 50vw, 100vw"
                alt={hero_title}
                className="rounded-md object-contain w-full h-full"
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
              sourceUrl="/api/products/bargain-carousel/"
              storeIds={anchorStoreIdsArray}
              companyName={company.name}
              isBargainCarousel={true}
              isDefaultStores={isDefaultStores}
              minProducts={1}
            />
          ))}
        </div>
      </div>

      {/* --- Bargain Stats Section --- */}
      <div className="container mx-auto px-4 py-2">
        <h2 className="text-3xl font-bold text-center my-8">
            Which supermarket is the <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">cheapest</span> in Australia?
        </h2>
        {isLoadingStats && <LoadingSpinner />}
        {isErrorStats && <p className="text-center text-red-500">Could not load bargain statistics.</p>}
        {bargainStats && (
            <div className="mt-4 flex flex-wrap -mx-2">
                {bargainStats.map((comparison, index) => (
                    <div key={index} className="w-full lg:w-1/2 px-2 mb-4">
                        <PriceComparisonChart comparison={comparison} categoryName="products" />
                    </div>
                ))}
                <div className="w-full lg:w-1/2 px-2 mb-4">
                    <Card className="h-full">
                      <CardHeader>
                        <CardTitle>How We Compare</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-col gap-2">
                          <p className="text-sm text-gray-700">
                            These statistics are based on the full set of identical products that two companies both sell according to our database.
                          </p>
                          <p className="text-sm text-gray-700">
                            You'll notice this number changes for each pairing. Companies like Aldi have a highly unique product range, which results in a smaller overlap and fewer items being compared. For IGA, stores are independently owned and prices vary, so we use the average IGA price for each product to make the comparison fair.
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                </div>
            </div>
        )}
      </div>

      {/* FAQ Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section>
            <FAQ
              title="Frequently Asked Questions about Bargains"
              page="bargains"
              imageSrc={snackLineup}
              srcSet={`${snackLineup320} 320w, ${snackLineup640} 640w, ${snackLineup768} 768w, ${snackLineup1024} 1024w, ${snackLineup1280} 1280w`}
              sizes="(min-width: 1024px) 50vw, 100vw"
              imageAlt="Snack Lineup"
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default BargainsPage;
