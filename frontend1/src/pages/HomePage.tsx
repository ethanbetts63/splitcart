import React from "react";
import { FaqAccordion } from "../components/FaqAccordion";
import { ProductCarousel } from "../components/ProductCarousel";
import { useStoreSelection } from "@/context/StoreContext";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import confusedShopper from "../assets/confused_shopper.png";
import kingKongImage from "../assets/king_kong.png";

const HomePage = () => {
  const { selectedStoreIds } = useStoreSelection();
  const storeIdsArray = Array.from(selectedStoreIds);

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

          <section>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div>
                <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">The Hard Hitting Questions</h2>
                <FaqAccordion />
              </div>
              <div>
                <AspectRatio ratio={16 / 9}>
                  <img src={kingKongImage} alt="King Kong swatting at discount planes" className="rounded-md object-contain w-full h-full" />
                </AspectRatio>
              </div>
            </div>
          </section>

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

      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900">
            Is ply count or per kilogram value more important for buying toilet paper?
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-lg text-gray-700">
          <div className="flex flex-col gap-4">
            <p>
              To many people this is a ridiculous thought. But if you're like me then you'll understand. You're probably the sort of person that has thought about the weight of chicken bones in a whole chicken. Or maybe even the real dollar value of a reward point. If you're like me then SplitCart is built for you. I know that to be a fact because I built SplitCart for me.
            </p>
            <p>
              The idea is simple. If we had 2 stores to shop at and a list of products, there's no way all the products could be cheaper at just 1 store. So why shop at just 1 store? Becuase, we didn't know what's cheapest where and figuring it out would've been a major hassle.
            </p>
          </div>
          <div className="flex flex-col gap-4">
            <p>
              Now we know, and I've taken care of as much hassle as possible. SplitCart is nothing short of a obsession for me and it's a pleasure to have you onboard for the ride. If you have questions, suggestions or anything else I'd love to hear from you.
            </p>
            <div>
              <p>Happy shopping,</p>
              <p>Ethan Betts.</p>
              <p>ethanbetts63@gmail.com</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;