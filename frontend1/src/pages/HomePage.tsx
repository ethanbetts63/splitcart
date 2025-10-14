import React from "react";
import { ProductCarousel } from "../components/ProductCarousel";
import { useStoreSelection } from "@/context/StoreContext";

const HomePage = () => {
  const { selectedStoreIds } = useStoreSelection();
  const storeIdsArray = Array.from(selectedStoreIds);

  return (
    <main className="p-4">
      <section className="mt-8">
        <h2 className="text-xl font-semibold">Bargains</h2>
        <ProductCarousel 
          sourceUrl="/api/products/bargains/?limit=20" 
          storeIds={storeIdsArray} 
        />
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Milk</h2>
        <ProductCarousel sourceUrl="/api/products/?search=milk&limit=20" />
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Eggs</h2>
        <ProductCarousel sourceUrl="/api/products/?search=eggs&limit=20" />
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Bread</h2>
        <ProductCarousel sourceUrl="/api/products/?search=bread&limit=20" />
      </section>
    </main>
  );
};

export default HomePage;