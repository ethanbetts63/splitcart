import React from 'react';
import { ProductCard } from "./ProductCard";
import '../css/ProductCarousel.css';

export function ProductCarousel() {
  return (
    <div className="custom-carousel">
      <div className="custom-carousel__container">
        {Array.from({ length: 10 }).map((_, index) => (
          <div className="custom-carousel__slide" key={index}>
            <ProductCard />
          </div>
        ))}
      </div>
    </div>
  );
}
