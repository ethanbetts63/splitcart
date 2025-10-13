import React from 'react';
import { NavigationMenu, NavigationMenuList, NavigationMenuItem, NavigationMenuLink } from "@/components/ui/navigation-menu";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel";

const ProductListPage = () => {
  return (
    <div>
      <NavigationMenu>
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink href="#">Home</NavigationMenuLink>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuLink href="#">About</NavigationMenuLink>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuLink href="#">Contact</NavigationMenuLink>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>

      <div className="grid grid-cols-2 gap-4 p-4">
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Instructions</CardTitle>
              <CardDescription>How to use the app</CardDescription>
            </CardHeader>
            <CardContent>
              <p>1. ...</p>
              <p>2. ...</p>
              <p>3. ...</p>
            </CardContent>
          </Card>
        </div>
        <div>
          <img src="https://placehold.co/600x400" alt="placeholder" />
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold my-4">Featured Products</h2>
        <Carousel>
          <CarouselContent>
            <CarouselItem>Product 1</CarouselItem>
            <CarouselItem>Product 2</CarouselItem>
            <CarouselItem>Product 3</CarouselItem>
            <CarouselItem>Product 4</CarouselItem>
            <CarouselItem>Product 5</CarouselItem>
          </CarouselContent>
          <CarouselPrevious />
          <CarouselNext />
        </Carousel>

        <h2 className="text-2xl font-bold my-4">On Sale</h2>
        <Carousel>
          <CarouselContent>
            <CarouselItem>Product 1</CarouselItem>
            <CarouselItem>Product 2</CarouselItem>
            <CarouselItem>Product 3</CarouselItem>
            <CarouselItem>Product 4</CarouselItem>
            <CarouselItem>Product 5</CarouselItem>
          </CarouselContent>
          <CarouselPrevious />
          <CarouselNext />
        </Carousel>
      </div>
    </div>
  );
};

export default ProductListPage;
