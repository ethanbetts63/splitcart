import React from 'react';
import useEmblaCarousel from 'embla-carousel-react';
import Autoplay from 'embla-carousel-autoplay';
import { ProductCard } from "./ProductCard";
import '../css/ProductCarousel.css';

export function ProductCarousel() {
  const [emblaRef] = useEmblaCarousel({ loop: true }, [Autoplay()]);

  return (
    <div className="embla" ref={emblaRef}>
      <div className="embla__container">
        {Array.from({ length: 10 }).map((_, index) => (
          <div className="embla__slide" key={index}>
            <ProductCard />
          </div>
        ))}
      </div>
    </div>
  );
}
