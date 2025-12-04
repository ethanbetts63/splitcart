import React from 'react';
import { useDocumentHead } from '@/hooks/useDocumentHead';
import { ProductCarousel } from "../components/ProductCarousel";
import { FAQ } from "../components/FAQ";
import { useStoreList } from "../context/StoreListContext";
import { AspectRatio } from "../components/ui/aspect-ratio";
import confusedShopper from "../assets/confused_shopper.webp";
import confusedShopper320 from "../assets/confused_shopper-320w.webp";
import confusedShopper640 from "../assets/confused_shopper-640w.webp";
import confusedShopper768 from "../assets/confused_shopper-768w.webp";
import confusedShopper1024 from "../assets/confused_shopper-1024w.webp";
import confusedShopper1280 from "../assets/confused_shopper-1280w.webp";
import kingKongImage from "../assets/king_kong.webp";
import kingKongImage320 from "../assets/king_kong-320w.webp";
import kingKongImage640 from "../assets/king_kong-640w.webp";
import kingKongImage768 from "../assets/king_kong-768w.webp";
import kingKongImage1024 from "../assets/king_kong-1024w.webp";
import kingKongImage1280 from "../assets/king_kong-1280w.webp";

const HomePage = () => {
  const { selectedStoreIds, anchorStoreMap, isUserDefinedList } = useStoreList();
  useDocumentHead(
    "SplitCart: Australian Grocery Price Comparison",
    "Every store has a deal — but finding them all takes forever. SplitCart automates discount hunting by comparing prices across Coles, Woolworths, Aldi and IGA and splitting your cart for the cheapest overall shop. One list, multiple stores, maximum savings."
  );

  const isDefaultStores = !isUserDefinedList;

  const anchorStoreIdsArray = React.useMemo(() => {
    const anchorIds = new Set<number>();
    for (const storeId of selectedStoreIds) {
      const anchorId = anchorStoreMap[storeId];
      if (anchorId) {
        anchorIds.add(anchorId);
      }
    }
    return Array.from(anchorIds);
  }, [selectedStoreIds, anchorStoreMap]);

  return (
    <div>
      {/* --- Hero Section --- */}
      <div className="container mx-auto px-4 pt-4 pb-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img 
                src={confusedShopper} 
                srcSet={`${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`}
                sizes="(min-width: 1024px) 50vw, calc(100vw - 2rem)"
                alt="Confused Shopper" 
                className="rounded-md object-cover w-full h-full"
                fetchPriority="high" />
            </AspectRatio>
          </div>
          <div className="text-left">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              They’ve been optimising for profit. Now it’s your turn.
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Every store has a deal — but finding them all takes forever. SplitCart automates discount hunting by comparing prices across supermarkets and splitting your cart for the cheapest overall shop. <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">One list, multiple stores, maximum savings.</span> Search or browse and add products to your cart to get started! Click "Next" in the bottom right when you're ready!
            </p>
          </div>
        </div>
      </div>

      {/* --- Carousel: Bargains --- */}
      <div className="container mx-auto px-4 py-8">
        <ProductCarousel
          key="bargains"
          title="Bargains"
          sourceUrl="/api/products/bargain-carousel/"
          storeIds={anchorStoreIdsArray}
          isDefaultStores={isDefaultStores}
        />
      </div>

      {/* --- Carousel: Snacks and Sweets --- */}
      <div className="container mx-auto px-4 py-8">
        <ProductCarousel
          key="snacks-and-sweets"
          title="Snacks & Sweets"
          sourceUrl="/api/products/"
          storeIds={anchorStoreIdsArray}
          primaryCategorySlugs={['snacks', 'sweets']}
          pillarPageLinkSlug="snacks-and-sweets"
          slot={0}
          isDefaultStores={isDefaultStores}
        />
      </div>

      {/* --- Letter Section --- */}
      <div className="container mx-auto px-4 md:px-16 pt-1 pb-1">
        <div className="text-center mb-8">
          <h2 className="text-5xl font-bold tracking-tight text-gray-900 max-w-2xl mx-auto">
            What percentage of a whole chicken is bone weight?
          </h2>
          <p className="text-xl mt-4">Short answer: <span className="font-bold">25-32%</span>. Most common answer: <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Who cares?</span></p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-12 text-lg ">
          <div className="flex flex-col gap-4">
            <p>
              <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">I care.</span> And if you're like me then you care too. If you're like me, you've considered the dollar value of a rewards point. Or weighed the merits of ply count versus the per kilo price of toilet paper.
            </p>
            <p className="font-bold">
              If you're like me then SplitCart was built for you. I know this to be a fact because I built SplitCart for me.
            </p>
            <p>
              The idea is simple. Why not buy each item in my shopping list from the store where it's cheapest? Becuase you don't know the price of every item in every store. Becuase you'd never go to ten stores on one shopping run. Becuase it would be a hassle.
            </p>
          </div>
          <div className="flex flex-col gap-4">
            <p>
              I've collected the prices. I've mathematically calculated the best two, three, or four store combinations, and I've removed as much hassle as humanly possible.
            </p>
            <p>
              So, welcome aboard fellow bargain hunter. I hope SplitCart can be as useful to you as it is to me. <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Expect to save 10-15%</span> on your grocery bill!
            </p>
            <p>
              If you have questions, suggestions or anything else I'd love to hear from you.
            </p>
            <div>
              <p>Happy hunting,</p>
              <p className="font-bold"><span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">Ethan Betts</span>, <a href="mailto:ethanbetts63@gmail.com" className="text-blue-600 hover:underline">ethanbetts63@gmail.com</a></p>
              <p className="italic text-sm text-gray-600">Founder and Developer</p>
            </div>
          </div>
        </div>
      </div>

      {/* --- Carousels: Meat, Seafood / Eggs, Dairy --- */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <ProductCarousel
            key="meat-and-seafood"
            title="Meat & Seafood"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['meat', 'seafood']}
            pillarPageLinkSlug="meat-and-seafood"
            slot={1}
            isDefaultStores={isDefaultStores}
          />
          <ProductCarousel
            key="dairy"
            title="Dairy"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['dairy']}
            pillarPageLinkSlug="dairy"
            slot={2}
            isDefaultStores={isDefaultStores}
          />
        </div>
      </div>
      
      {/* --- FAQ Section --- */}
      <div className="container mx-auto px-4 py-8">
        <section>
          <FAQ
            title="The Hard Hitting Questions"
            page="home"
            imageSrc={kingKongImage}
            srcSet={`${kingKongImage320} 320w, ${kingKongImage640} 640w, ${kingKongImage768} 768w, ${kingKongImage1024} 1024w, ${kingKongImage1280} 1280w`}
            sizes="(min-width: 1024px) 50vw, calc(100vw - 2rem)"
            imageAlt="King Kong swatting at discount planes"
          />
        </section>
      </div>

      {/* --- Carousels: Fruit, Veg, Spices / Pantry, International / Health, Beauty, Supplements --- */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <ProductCarousel
            key="fruit-veg-and-spices"
            title="Fruit, Veg & Spices"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['fruit', 'veg', 'spices']}
            pillarPageLinkSlug="fruit-veg-and-spices"
            slot={3}
            isDefaultStores={isDefaultStores}
          />
          <ProductCarousel
            key="pantry-and-international"
            title="Pantry & International"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['pantry', 'international']}
            pillarPageLinkSlug="pantry-and-international"
            slot={4}
            isDefaultStores={isDefaultStores}
          />
          <ProductCarousel
            key="health-beauty-and-supplements"
            title="Health, Beauty & Supplements"
            sourceUrl="/api/products/"
            storeIds={anchorStoreIdsArray}
            primaryCategorySlugs={['health', 'beauty', 'health-foods']}
            pillarPageLinkSlug="health-beauty-and-supplements"
            slot={5}
            isDefaultStores={isDefaultStores}
          />
        </div>
      </div>
    </div>
  );
};

export default HomePage;
