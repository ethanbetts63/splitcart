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
import { FAQ } from "../components/FAQ";
import { useApiQuery } from '../hooks/useApiQuery';
import type { PriceComparison, Product } from '../types';
import PriceComparisonChart from '../components/PriceComparisonChart';
import LoadingSpinner from '../components/LoadingSpinner';

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
  ];

  // --- Fetching and Sorting Bargains ---
  const { data: bargainProductResponse, isLoading: isLoadingBargains } = useApiQuery<Product[]>(
    ['bargains', storeIdsArray, 60],
    `/api/products/bargain-carousel/?store_ids=${storeIdsArray.join(',')}&limit=60`,
    {},
    { enabled: storeIdsArray.length > 0 }
  );

  const sortedBargains = React.useMemo(() => {
    const companyBargains: { [key: string]: Product[] } = {
      Coles: [],
      Woolworths: [],
      Aldi: [],
      Iga: [],
    };

    const products = Array.isArray(bargainProductResponse) 
      ? bargainProductResponse 
      : bargainProductResponse?.results;

    if (products) {
      // Group products by the company name in bargain_info
      products.forEach(product => {
        if (product.bargain_info?.cheapest_company_name) {
          const companyName = product.bargain_info.cheapest_company_name;
          if (companyBargains.hasOwnProperty(companyName)) {
            companyBargains[companyName].push(product);
          }
        }
      });

      // Sort products within each company's array by discount percentage
      for (const companyName in companyBargains) {
        companyBargains[companyName].sort((a, b) => {
          const discountA = a.bargain_info?.discount_percentage ?? 0;
          const discountB = b.bargain_info?.discount_percentage ?? 0;
          return discountB - discountA; // Sort descending
        });
      }
    }
    return companyBargains;
  }, [bargainProductResponse]);


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
          {isLoadingBargains ? (
            companies.map(company => (
              <ProductCarousel
                key={company.id}
                title={`${company.name} Bargains`}
                isLoading={true}
              />
            ))
          ) : (
            companies.map(company => (
              sortedBargains[company.name] && sortedBargains[company.name].length > 0 && (
                <ProductCarousel
                  key={company.id}
                  title={`${company.name} Bargains`}
                  products={sortedBargains[company.name]}
                  storeIds={storeIdsArray}
                  isDefaultStores={isDefaultStores}
                />
              )
            ))
          )}
        </div>
      </div>

      {/* --- Bargain Stats Section --- */}
      <div className="container mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold text-center mb-8">Bargain Breakdown</h2>
        {isLoadingStats && <LoadingSpinner />}
        {isErrorStats && <p className="text-center text-red-500">Could not load bargain statistics.</p>}
        {bargainStats && (
            <div className="mt-4 flex flex-wrap -mx-2">
                {bargainStats.map((comparison, index) => (
                    <div key={index} className="w-full lg:w-1/2 px-2 mb-4">
                        <PriceComparisonChart comparison={comparison} categoryName="products" />
                    </div>
                ))}
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
              imageSrc={confusedShopper}
              srcSet={`${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`}
              sizes="(min-width: 1024px) 50vw, 100vw"
              imageAlt="Confused Shopper"
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default BargainsPage;
