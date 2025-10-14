"use client"

import * as React from "react"
import {
  Home,
  MapPin,
  ShoppingCart,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar"
import EditLocationPage from "@/pages/dialog-pages/EditLocationPage";
import TrolleyPage from "@/pages/dialog-pages/TrolleyPage";

// Define a type for our navigation items
type NavItem = {
  name: string;
  icon: React.ElementType;
};

const data = {
  nav: [
    { name: "Trolley", icon: ShoppingCart },
    { name: "Edit Location", icon: MapPin },
    { name: "Home", icon: Home },
  ],
}

// A component to render the correct page content based on the active page
const PageContent = ({ activePage }: { activePage: string }) => {
  switch (activePage) {
    case 'Trolley':
      return <TrolleyPage />;
    case 'Edit Location':
      return <EditLocationPage />;
    default:
      return (
        <div className="p-4">
          <h2 className="text-xl font-semibold">{activePage}</h2>
          <p>Content for {activePage} goes here.</p>
        </div>
      );
  }
};

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultPage?: string;
}

export function SettingsDialog({ open, onOpenChange, defaultPage = 'Trolley' }: SettingsDialogProps) {
  const [activePage, setActivePage] = React.useState(defaultPage);

  // When the dialog opens, ensure it shows the correct page
  React.useEffect(() => {
    if (open) {
      setActivePage(defaultPage);
    }
  }, [open, defaultPage]);

  const handleNavClick = (e: React.MouseEvent, pageName: string) => {
    e.preventDefault();
    setActivePage(pageName);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden md:max-h-[500px] md:max-w-[700px] lg:max-w-[800px]">
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <DialogDescription className="sr-only">
          Customize your settings here.
        </DialogDescription>
        <SidebarProvider className="items-start">
          <Sidebar collapsible="none" className="hidden md:flex">
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {data.nav.map((item: NavItem) => (
                      <SidebarMenuItem key={item.name}>
                        <SidebarMenuButton
                          asChild
                          isActive={item.name === activePage}
                        >
                          <a href="#" onClick={(e) => handleNavClick(e, item.name)}>
                            <item.icon />
                            <span>{item.name}</span>
                          </a>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>
          </Sidebar>
          <main className="flex h-[480px] flex-1 flex-col overflow-hidden">
            <PageContent activePage={activePage} />
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  )
}