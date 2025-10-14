import React from "react";
import { ProductCarousel } from "../components/ProductCarousel";

const HomePage = () => {
  return (
    <main className="container mx-auto p-4">
      <section className="mt-8">
        <h2 className="text-xl font-semibold">Featured Products</h2>
        <ProductCarousel sourceUrl="/api/products/?limit=20&ordering=-id" />
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">New Arrivals</h2>
        <ProductCarousel sourceUrl="/api/products/?limit=20&ordering=-created_at" />
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">On Sale</h2>
        <ProductCarousel sourceUrl="/api/products/bargains/?limit=20" />
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Popular</h2>
        <ProductCarousel sourceUrl="/api/products/?limit=20&ordering=-popularity" />
      </section>
    </main>
  );
};

export default HomePage;