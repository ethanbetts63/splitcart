"use client"

import * as React from "react"
import {
  Home,
  MapPin,
  ShoppingCart,
  X, // Import the X icon
} from "lucide-react"

import { useStoreList } from "../context/StoreListContext";
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
import EditLocationPage from "../pages/dialog-pages/EditLocationPage";
import CartPage from "../pages/dialog-pages/CartPage";
import { toast } from "sonner";

// Utility function to compare two sets
function areSetsEqual<T>(a: Set<T>, b: Set<T>): boolean {
  if (a.size !== b.size) {
    return false;
  }
  for (const item of a) {
    if (!b.has(item)) {
      return false;
    }
  }
  return true;
}

// Define a type for our navigation items
type NavItem = {
  name: string;
  icon: React.ElementType;
  isCloseButton?: boolean; // Add a flag for the close button
};

const data = {
  nav: [
    { name: "Close", icon: X, isCloseButton: true }, // Add the close button to the nav
    { name: "cart", icon: ShoppingCart },
    { name: "Edit Location", icon: MapPin },
    { name: "Home", icon: Home },
  ],
}

// A component to render the correct page content based on the active page
const PageContent = ({ 
  activePage, 
  onOpenChange, 
  localSelectedStoreIds, 
  setLocalSelectedStoreIds,
  setHasSearchOccurred
}: { 
  activePage: string, 
  onOpenChange: (open: boolean) => void,
  localSelectedStoreIds: Set<number>,
  setLocalSelectedStoreIds: React.Dispatch<React.SetStateAction<Set<number>>>,
  setHasSearchOccurred: React.Dispatch<React.SetStateAction<boolean>>
}) => {
  switch (activePage) {
    case 'cart':
      return <CartPage onOpenChange={onOpenChange} />;
    case 'Edit Location':
      return <EditLocationPage 
                localSelectedStoreIds={localSelectedStoreIds} 
                setLocalSelectedStoreIds={setLocalSelectedStoreIds} 
                onOpenChange={onOpenChange}
                setHasSearchOccurred={setHasSearchOccurred}
             />;
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

export function SettingsDialog({ open, onOpenChange, defaultPage = 'cart' }: SettingsDialogProps) {
  const [activePage, setActivePage] = React.useState(defaultPage);
  const { selectedStoreIds, setSelectedStoreIds, saveStoreList, currentStoreListName } = useStoreList();
  const [localSelectedStoreIds, setLocalSelectedStoreIds] = React.useState<Set<number>>(selectedStoreIds);
  // Rename to indicate it's intentionally not read
  const [_localChangesMade, setLocalChangesMade] = React.useState(false); 

  // When the defaultPage prop changes, update the activePage state.
  React.useEffect(() => {
    setActivePage(defaultPage);
  }, [defaultPage]);

  // When the dialog opens, sync the local state with the global state.
  React.useEffect(() => {
    if (open) {
      setLocalSelectedStoreIds(new Set(selectedStoreIds));
      setLocalChangesMade(false); // Reset changes made flag when opening
    }
  }, [open, selectedStoreIds]);
  
  // Effect to track local changes for performance/save logic
  React.useEffect(() => {
    // Only set localChangesMade to true if localSelectedStoreIds actually differs from global
    // after the initial sync from 'selectedStoreIds'.
    // This prevents it from being true immediately on opening if there are no changes.
    if (open && !areSetsEqual(localSelectedStoreIds, selectedStoreIds)) {
        setLocalChangesMade(true);
    }
  }, [localSelectedStoreIds, open, selectedStoreIds]);


  const handleNavClick = (pageName: string) => {
    setActivePage(pageName);
  };

  const handleOpenChange = (newOpenState: boolean) => {
    // If trying to close the dialog
    if (!newOpenState) {
      // and we are on the Edit Location page and no stores are selected
      if (activePage === 'Edit Location' && localSelectedStoreIds.size === 0) {
        toast.warning("You must select a location to continue.", { position: "top-center" });
        return; // Prevent closing
      }

      // Always update global state when closing the dialog to reflect the latest local selection
      setSelectedStoreIds(localSelectedStoreIds);

      // Only save to backend if the local selected stores are actually different from the global ones
      // This implicitly covers explicit searches and manual selections.
      if (!areSetsEqual(localSelectedStoreIds, selectedStoreIds)) {
        saveStoreList(currentStoreListName, Array.from(localSelectedStoreIds));
      }
    }
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
            <PageContent 
              activePage={activePage} 
              onOpenChange={handleOpenChange} 
              localSelectedStoreIds={localSelectedStoreIds}
              setLocalSelectedStoreIds={setLocalSelectedStoreIds}
              setHasSearchOccurred={setLocalChangesMade} // Pass the localChangesMade setter
            />
          </main>
        </SidebarProvider>
      </DialogContent>
    </Dialog>
  )
}