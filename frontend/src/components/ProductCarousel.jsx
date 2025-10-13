import React from 'react';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import { ProductCard } from "./ProductCard";

export function ProductCarousel() {
  return (
    <Carousel
      opts={{
        align: "start",
      }}
      className="w-full"
    >
      <CarouselContent className="-ml-1 py-4">
        {Array.from({ length: 10 }).map((_, index) => (
          <CarouselItem key={index} className="pl-1 basis-1/2 sm:basis-1/3 md:basis-1/4 lg:basis-1/5">
            <ProductCard />
          </CarouselItem>
        ))}
      </CarouselContent>
    </Carousel>
  );
}
