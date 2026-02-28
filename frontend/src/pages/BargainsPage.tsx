import React from 'react';
import { AspectRatio } from '../components/ui/aspect-ratio';
import sizeComparison from "../assets/size_comparison.png";
import sizeComparison320 from "../assets/size_comparison-320w.webp";
import sizeComparison640 from "../assets/size_comparison-640w.webp";
import sizeComparison768 from "../assets/size_comparison-768w.webp";
import sizeComparison1024 from "../assets/size_comparison-1024w.webp";
import sizeComparison1280 from "../assets/size_comparison-1280w.webp";

import { useStoreList } from '../context/StoreListContext';
import { ProductCarousel } from "../components/ProductCarousel";
import { FAQ } from "../components/FAQ";
import { useApiQuery } from '../hooks/useApiQuery';
import type { PriceComparison } from '../types';
import PriceComparisonChart from '../components/PriceComparisonChart';
import LoadingSpinner from '../components/LoadingSpinner';

import snackLineup from "../assets/snack_lineup.webp";
import snackLineup320 from "../assets/snack_lineup-320w.webp"; 
import snackLineup640 from "../assets/snack_lineup-640w.webp"; 
import snackLineup768 from "../assets/snack_lineup-768w.webp"; 
import snackLineup1024 from "../assets/snack_lineup-1024w.webp"; 
import snackLineup1280 from "../assets/snack_lineup-1280w.webp";

import Seo from '../components/Seo';

const bargainsFaqs = [
  {
    question: "Coles vs Woolworths vs Aldi: Who has the best discounts?",
    answer: "Aldi is generally cheaper upfront, so it doesn't need the heavy, frequent discounting you see elsewhere. It does run some discounts on food items, but they're smaller, less frequent, and not tied to big-brand promotions. One of the main reasons is that Aldi's range is mostly private-label and unique, so it doesn't participate in the same supplier-funded discount system that drives specials at Coles and Woolworths. Coles and Woolworths work on predictable 4–8 week discount cycles, where major branded products regularly drop to half price. These specials are usually subsidised by the brands, who pay for catalogue placement and fund much of the price reduction in exchange for higher volume. Because both supermarkets rely on the same suppliers, their specials end up looking almost identical each week. So overall, Aldi offers lower everyday prices with light discounting, while Coles and Woolworths offer the biggest promotions—but largely because brands are paying for them, not the supermarkets themselves."
  },
  {
    question: "When do expiring products get discounted at Aldi?",
    answer: "ALDI's clearance process is different, focusing on earlier, fixed-rate markdowns rather than a late-night final sweep. An official policy is that most fresh food—including meat, dairy, and ready meals—is marked down by 20% two days before its expiry date, with most markdowns typically completed before 6:00 PM. ALDI bakery goods are often prioritized for donation. Your best strategy is to look for the red sticker items around 5-6pm but markdown strategies can vary widely store to store as per the managers discretion."
  },
  {
    question: "When do expiring products get discounted at Coles?",
    answer: "The final and most significant markdowns at Coles often appear between 7:00 PM and 8:00 PM, particularly at stores with a 9:00 PM closing time. Coles staff tend to perform a large reduction sweep in the hours immediately before the store closes to ensure minimal waste, focusing on high-value items like meat, deli goods, and hot roast chickens (which are reduced 4 hours after cooking). The specific final time can vary, so shoppers should check their local store's schedule or look for staff clearing items with a trolley in the late evening."
  },
  {
    question: "When do expiring products get discounted at Woolworths?",
    answer: "Woolworths generally uses a progressive markdown schedule, with the deepest discounts occurring in the late afternoon and evening. The best time to hunt for the maximum reduction (often 50% to 80% off on meat, chilled meals, and dairy) is typically after 6:00 PM and up to one hour before closing. Earlier in the day (around 2:00 PM to 4:00 PM) you will find initial, smaller markdowns (20% to 40% off), but the staff perform the final, aggressive reduction sweep in the evening to clear items expiring that day."
  },
  {
    question: "When do expiring products get discounted at IGA?",
    answer: "Since IGA stores are independently owned, there is no single markdown schedule. Discounts are highly dependent on the local store manager and the volume of stock. Some stores follow the evening trend, marking down items after 5:00 PM, while others apply reductions first thing in the morning. To find the best deals, you should check if your local IGA uses markdown apps like FoodHero or Gander, or simply ask a staff member when their department typically applies the 'Reduced to Clear' stickers."
  },
];

const BargainsPage: React.FC = () => {
    const title = "SplitCart: Australia's Best Grocery Bargains";
    const description = "Find the best grocery bargains in Australia. SplitCart compares prices across Coles, Woolworths, Aldi, and IGA to find you the biggest discounts.";

    const webPageSchema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": "https://www.splitcart.com.au/bargains",
    };

  const hero_title = "Australia's Best Grocery Bargains";

  const { selectedStoreIds, anchorStoreMap, isUserDefinedList } = useStoreList();

  const anchorStoreIdsArray = React.useMemo(() => {
    if (!anchorStoreMap) {
      return Array.from(selectedStoreIds);
    }
    const anchorIds = new Set<number>();
    for (const storeId of selectedStoreIds) {
      const anchorId = anchorStoreMap[storeId];
      if (anchorId) {
        anchorIds.add(anchorId);
      }
    }
    return Array.from(anchorIds);
  }, [selectedStoreIds, anchorStoreMap]);
  
  const isDefaultStores = !isUserDefinedList; // This is still needed for ProductCarousel prop
  
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
      <Seo
        title={title}
        description={description}
        canonicalPath="/bargains"
        structuredData={webPageSchema}
      />
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img
                src={sizeComparison}
                srcSet={`${sizeComparison320} 320w, ${sizeComparison640} 640w, ${sizeComparison768} 768w, ${sizeComparison1024} 1024w, ${sizeComparison1280} 1280w`}
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
              Forget the flashy ‘specials’ — these are the real bargains hiding in plain sight. We’ve compared prices across supermarkets to show you who actually sells each item for less. <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Interested in the stats?</span> We've graphed the trends below so you can see which supermarket comes out on top overall.
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
      <div className="container mx-auto px-4 py-8">
        <section className="-mx-4 md:mx-0 bg-gray-50 py-8 md:px-5 rounded-none md:rounded-xl">
          <h2 className="text-3xl font-bold text-center mb-8 px-5 md:px-0">
            Which supermarket is the <span className="bg-yellow-300 px-0.5 py-1 rounded italic text-black">cheapest</span> in Australia?
          </h2>
          {isLoadingStats && <LoadingSpinner />}
          {isErrorStats && <p className="text-center text-red-500">Could not load bargain statistics.</p>}
          {bargainStats && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 px-4 md:px-0">
              {bargainStats.map((comparison, index) => (
                <PriceComparisonChart key={index} comparison={comparison} categoryName="products" />
              ))}
              <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-5 flex flex-col gap-3">
                <h3 className="font-bold text-gray-900 text-base">How We Compare</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  These statistics are based on the full set of identical products that two companies both sell according to our database.
                </p>
                <p className="text-sm text-gray-600 leading-relaxed">
                  You'll notice this number changes for each pairing. Companies like Aldi have a highly unique product range, which results in a smaller overlap and fewer items being compared. For IGA, stores are independently owned and prices vary, so we use the average IGA price for each product to make the comparison fair.
                </p>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* FAQ Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section>
            <FAQ
              title="Frequently Asked Questions about Bargains"
              faqs={bargainsFaqs}
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
