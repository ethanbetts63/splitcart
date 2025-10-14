"use client"

import * as React from "react"
import {
  Bell,
  Check,
  Globe,
  Home,
  Keyboard,
  Link,
  Lock,
  Menu,
  MessageCircle,
  Paintbrush,
  Settings,
  Video,
  MapPin, // Added for Edit Location
} from "lucide-react"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
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
import EditLocationPage from "@/pages/dialog-pages/EditLocationPage"; // Import the new page

// Define a type for our navigation items
type NavItem = {
  name: string;
  icon: React.ElementType;
};

const data = {
  nav: [
    { name: "Edit Location", icon: MapPin }, // Added new page
    { name: "Notifications", icon: Bell },
    { name: "Navigation", icon: Menu },
    { name: "Home", icon: Home },
    { name: "Appearance", icon: Paintbrush },
    { name: "Messages & media", icon: MessageCircle },
    { name: "Language & region", icon: Globe },
    { name: "Accessibility", icon: Keyboard },
    { name: "Mark as read", icon: Check },
    { name: "Audio & video", icon: Video },
    { name: "Connected accounts", icon: Link },
    { name: "Privacy & visibility", icon: Lock },
    { name: "Advanced", icon: Settings },
  ],
}

// Content for the default page
const MessagesMediaPage = () => (
  <>
    <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
      <div className="flex items-center gap-2 px-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem className="hidden md:block">
              <BreadcrumbLink href="#">Settings</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="hidden md:block" />
            <BreadcrumbItem>
              <BreadcrumbPage>Messages & media</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4 pt-0">
      {Array.from({ length: 10 }).map((_, i) => (
        <div
          key={i}
          className="bg-muted/50 aspect-video max-w-3xl rounded-xl"
        />
      ))}
    </div>
  </>
);

// A component to render the correct page content based on the active page
const PageContent = ({ activePage }: { activePage: string }) => {
  switch (activePage) {
    case 'Edit Location':
      return <EditLocationPage />;
    case 'Messages & media':
      return <MessagesMediaPage />;
    default:
      return (
        <div className="p-4">
          <h2 className="text-xl font-semibold">{activePage}</h2>
          <p>Content for {activePage} goes here.</p>
        </div>
      );
  }
};

export function SettingsDialog() {
  const [open, setOpen] = React.useState(false) // Default to closed
  const [activePage, setActivePage] = React.useState('Edit Location'); // Default to our new page

  const handleNavClick = (e: React.MouseEvent, pageName: string) => {
    e.preventDefault();
    setActivePage(pageName);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">Settings</Button>
      </DialogTrigger>
      <DialogContent className="overflow-hidden p-0 md:max-h-[500px] md:max-w-[700px] lg:max-w-[800px]">
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