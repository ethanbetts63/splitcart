import React from "react";
import { ProductCarousel } from "../components/ProductCarousel";
import { useStoreSelection } from "@/context/StoreContext";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import confusedShopper from "../assets/confused_shopper.png";

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
              SplitCart compares prices across major Australian supermarkets to find you the best deals. Simply create your shopping list, and we'll show you how to split your cart for maximum savings. Search above or browse below and add products to your cart to get started!
            </p>
          </div>
        </div>
      </div>

      <div className="px-8 pb-8 pt-4">
        <div className="bg-muted p-8 rounded-lg">
          <section>
            <ProductCarousel 
              title="Bargains"
              searchQuery="bargains"
              sourceUrl="/api/products/bargains/?limit=20" 
              storeIds={storeIdsArray} 
            />
          </section>

          <section className="mt-8">
            <ProductCarousel 
              title="Milk"
              searchQuery="milk"
              sourceUrl="/api/products/?search=milk&limit=20" 
              storeIds={storeIdsArray} 
            />
          </section>

          <section className="mt-8">
            <ProductCarousel 
              title="Eggs"
              searchQuery="eggs"
              sourceUrl="/api/products/?search=eggs&limit=20" 
              storeIds={storeIdsArray} 
            />
          </section>

          <section className="mt-8">
            <ProductCarousel 
              title="Bread"
              searchQuery="bread"
              sourceUrl="/api/products/?search=bread&limit=20" 
              storeIds={storeIdsArray} 
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default HomePage;