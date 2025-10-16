import React from "react";
import { ProductCarousel } from "../components/ProductCarousel";
import { useStoreSelection } from "@/context/StoreContext";

const HomePage = () => {
  const { selectedStoreIds } = useStoreSelection();
  const storeIdsArray = Array.from(selectedStoreIds);

  return (
    <div className="p-16">
      <section className="mt-8">
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
  );
};

export default HomePage;