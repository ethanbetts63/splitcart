"use client"

import * as React from "react"
import {
  Home,
  ShoppingCart,
  X,
} from "lucide-react"

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "./ui/dialog"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "./ui/sidebar"
import CartPage from "../page_components/dialog-pages/CartPage";
import type { NavItem } from "../types/NavItem";
import type { SettingsDialogProps } from "../types/SettingsDialogProps";

const data = {
  nav: [
    { name: "Close", icon: X, isCloseButton: true },
    { name: "cart", icon: ShoppingCart },
    { name: "Home", icon: Home },
  ],
}

const PageContent = ({ activePage, onOpenChange }: { activePage: string, onOpenChange: (open: boolean) => void }) => {
  switch (activePage) {
    case 'cart':
      return <CartPage onOpenChange={onOpenChange} />;
    default:
      return (
        <div className="p-4">
          <h2 className="text-xl font-semibold">{activePage}</h2>
          <p>Content for {activePage} goes here.</p>
        </div>
      );
  }
};

export function SettingsDialog({ open, onOpenChange, defaultPage = 'cart' }: SettingsDialogProps) {
  const [activePage, setActivePage] = React.useState(defaultPage);

  React.useEffect(() => {
    setActivePage(defaultPage);
  }, [defaultPage]);

  const handleNavClick = (pageName: string) => {
    setActivePage(pageName);
  };

  const handleOpenChange = (newOpenState: boolean) => {
    onOpenChange(newOpenState);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent 
        showCloseButton={false} // Disable the default close button
        className="overflow-hidden p-0 max-h-[500px] md:max-w-[700px] lg:max-w-[800px]"
      >
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <DialogDescription className="sr-only">
          Customize your settings here.
        </DialogDescription>
        <SidebarProvider className="items-start">
          <Sidebar collapsible="none" className="flex">
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {data.nav.map((item: NavItem) => (
                      <SidebarMenuItem key={item.name}>
                        <SidebarMenuButton
                          asChild
                          isActive={!item.isCloseButton && item.name === activePage}
                          tooltip={item.name}
                          className={item.isCloseButton ? "text-red-500 hover:bg-red-100 hover:text-red-600" : ""}
                        >
                          <button onClick={() => {
                            if (item.isCloseButton) {
                              handleOpenChange(false);
                            } else {
                              handleNavClick(item.name)
                            }
                          }}>
                            <item.icon />
                          </button>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>
          </Sidebar>
          <main className="absolute inset-y-0 left-12 right-0 overflow-y-auto">
            <PageContent activePage={activePage} onOpenChange={handleOpenChange} />
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  )
}
