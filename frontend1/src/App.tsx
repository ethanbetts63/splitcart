import React from "react";
import { cn } from "@/lib/utils";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu";
import { ProductCarousel } from "./components/ProductCarousel";
import './App.css';

function App() {
  return (
    <div>
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 hidden md:flex">
            <a href="/" className="mr-6 flex items-center space-x-2">
              <span className="hidden font-bold sm:inline-block">SplitCart</span>
            </a>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <NavigationMenu>
                <NavigationMenuList>
                  <NavigationMenuItem>
                    <NavigationMenuTrigger>Getting Started</NavigationMenuTrigger>
                    <NavigationMenuContent>
                      <ul className="grid gap-3 p-6 md:w-[400px] lg:w-[500px] lg:grid-cols-[.75fr_1fr]">
                        <li className="row-span-3">
                          <NavigationMenuLink asChild>
                            <a
                              className="flex h-full w-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-muted/50 to-muted p-6 no-underline outline-none focus:shadow-md"
                              href="/"
                            >
                              <div className="mb-2 mt-4 text-lg font-medium">
                                SplitCart
                              </div>
                              <p className="text-sm leading-tight text-muted-foreground">
                                Compare grocery prices and save money.
                              </p>
                            </a>
                          </NavigationMenuLink>
                        </li>
                        <ListItem href="/bargains" title="Bargains">
                          Find the best deals across all stores.
                        </ListItem>
                        <ListItem href="/products" title="Products">
                          Browse and search for products.
                        </ListItem>
                        <ListItem href="/stores" title="Stores">
                          See which stores are supported.
                        </ListItem>
                      </ul>
                    </NavigationMenuContent>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <a href="/about">
                      <NavigationMenuLink className="font-medium">
                        About
                      </NavigationMenuLink>
                    </a>
                  </NavigationMenuItem>
                </NavigationMenuList>
              </NavigationMenu>
            </nav>
          </div>
        </div>
      </header>
      <main className="container mx-auto p-4">
        <section className="mt-8">
          <h2 className="text-xl font-semibold">Featured Products</h2>
          <ProductCarousel />
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">New Arrivals</h2>
          <ProductCarousel />
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">On Sale</h2>
          <ProductCarousel />
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">Popular</h2>
          <ProductCarousel />
        </section>
      </main>
    </div>
  );
}

const ListItem = React.forwardRef<
  React.ElementRef<"a">,
  React.ComponentPropsWithoutRef<"a">
>(({ className, title, children, ...props }, ref) => {
  return (
    <li>
      <NavigationMenuLink asChild>
        <a
          ref={ref}
          className={cn(
            "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
            className
          )}
          {...props}
        >
          <div className="text-sm font-medium leading-none">{title}</div>
          <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
            {children}
          </p>
        </a>
      </NavigationMenuLink>
    </li>
  );
});
ListItem.displayName = "ListItem";

export default App;