import React, { useMemo } from 'react';
import { ProductCarousel } from "../components/ProductCarousel";
import { FaqImageSection } from "../components/FaqImageSection";
import { useStoreList } from "@/context/StoreListContext";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import confusedShopper from "../assets/confused_shopper.png";
import kingKongImage from "../assets/king_kong.png";

const HomePage = () => {
  const { selectedStoreIds } = useStoreList();
  const storeIdsArray = React.useMemo(() => Array.from(selectedStoreIds), [selectedStoreIds]);

  return (
    <div>
      <div className="container mx-auto px-4 pt-8 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div>
            <AspectRatio ratio={16 / 9}>
              <img src={confusedShopper} alt="Confused Shopper" className="rounded-md object-cover w-full h-full" />
            </AspectRatio>
          </div>
          <div className="text-left">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              They’ve been optimizing for profit. Now it’s your turn.
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Every store has a deal — but finding them all takes forever. SplitCart automates that process by comparing prices across supermarkets and splitting your cart for the cheapest overall shop. One list, multiple stores, maximum savings. Search or browse and add products to your cart to get started! Click "Next" in the top right when you're ready!
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section className="bg-muted p-8 rounded-lg">
            <ProductCarousel
              title="Bargains"
              searchQuery="bargains"
              sourceUrl="/api/products/bargains/?limit=20"
              storeIds={storeIdsArray}
            />
          </section>
        </div>
      </div>

      <div className="container mx-auto px-4 md:px-16 pt-8 pb-16">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 max-w-2xl mx-auto">
            What percentage of a whole chicken is bone weight?
          </h2>
          <p className="text-lg mt-4">Short answer: <span className="font-bold">25-32%</span>. Most common answer: <span className="font-bold">Who cares?</span></p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-lg ">
          <div className="flex flex-col gap-4">
            <p>
              <span className="font-bold">I care. </span>And if you're like me then you care too. If you're like me, you've considered the dollar value of a rewards point. Or weighed the merits of ply count versus the per kilo price of toilet paper.
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
              So, welcome aboard fellow bargain hunter. I hope SplitCart can be as useful to you as it is to me. <span className="font-bold bg-yellow-200 px-0.5 py-1 rounded">Expect to save 10-15%</span> on your grocery bill!
            </p>
            <p>
              If you have questions, suggestions or anything else I'd love to hear from you.
            </p>
            <div>
              <p>Happy hunting,</p>
              <p className="font-bold">Ethan Betts, <a href="mailto:ethanbetts63@gmail.com" className="text-blue-600 hover:underline">ethanbetts63@gmail.com</a></p>
              <p className="italic text-sm text-gray-600">Founder and Developer</p>
              
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section className="bg-muted p-8 rounded-lg">
            <ProductCarousel
              title="Milk"
              searchQuery="milk"
              sourceUrl="/api/products/?search=milk&limit=20"
              storeIds={storeIdsArray}
            />
          </section>

          <section className="bg-muted p-8 rounded-lg">
            <ProductCarousel
              title="Eggs"
              searchQuery="eggs"
              sourceUrl="/api/products/?search=eggs&limit=20"
              storeIds={storeIdsArray}
            />
          </section>

          <section className="bg-muted p-8 rounded-lg">
            <ProductCarousel
              title="Bread"
              searchQuery="bread"
              sourceUrl="/api/products/?search=bread&limit=20"
              storeIds={storeIdsArray}
            />
          </section>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section>
            <FaqImageSection
              title="The Hard Hitting Questions"
              page="home"
              imageSrc={kingKongImage}
              imageAlt="King Kong swatting at discount planes"
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default HomePage;