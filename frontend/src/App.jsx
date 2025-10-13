import React from 'react';
import { Header } from './components/Header';
import { ProductCarousel } from './components/ProductCarousel';
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
} from './components/ui/sidebar';

function App() {
  return (
    <SidebarProvider>
      <div className="flex">
        <Sidebar>
          <SidebarHeader>
            <h2 className="text-lg font-semibold">SplitCart</h2>
          </SidebarHeader>
          <SidebarContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>Home</SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>Products</SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>Bargains</SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarContent>
          <SidebarFooter>
            <p>Footer</p>
          </SidebarFooter>
        </Sidebar>
        <SidebarInset>
          <Header />
          <main className="container mx-auto p-4">
            <h1 className="text-2xl font-bold">Welcome to SplitCart</h1>
            <p>Your grocery comparison tool.</p>

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
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}

export default App;