"use client";

import { lazy, Suspense, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { SettingsDialog } from "@/components/settings-dialog";
import { useStoreList } from "@/context/StoreListContext";
import { useCart } from "@/context/CartContext";
import { useDialog } from "@/context/DialogContext";
import { useAuth } from "@/context/AuthContext";
import CategoryBar from "@/components/CategoryBar";
import Footer from "@/components/Footer";
import LoadingSpinner from "@/components/LoadingSpinner";
import NavBar from "@/components/NavBar";
import NextButton from "@/components/NextButton";

const Toaster = lazy(() =>
  import("@/components/ui/sonner").then((module) => ({ default: module.Toaster }))
);

export function AppShell({ children }: { children: ReactNode }) {
  const [searchTerm, setSearchTerm] = useState("");
  const router = useRouter();
  const pathname = usePathname() ?? "";
  const { selectedStoreIds, isUserDefinedList } = useStoreList();
  const { currentCart } = useCart();
  const { isAuthenticated, logout } = useAuth();
  const { isDialogOpen, dialogPage, openDialog, closeDialog } = useDialog();

  const items = currentCart ? currentCart.items : [];
  const cartTotal = items.length;

  const showCategoryBar =
    pathname === "/" ||
    pathname === "/search" ||
    pathname.startsWith("/categories/") ||
    pathname.startsWith("/product/");

  const showNextButton =
    (pathname === "/" ||
      pathname === "/search" ||
      pathname.startsWith("/categories/") ||
      pathname.startsWith("/product/") ||
      pathname === "/bargains") &&
    cartTotal > 0 &&
    !isDialogOpen;

  const handleSearch = () => {
    if (searchTerm.trim() !== "") {
      router.push(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  const handleSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      handleSearch();
    }
  };

  const handleOpenDialog = (page: string) => {
    if (page === "cart" && selectedStoreIds.size === 0) {
      openDialog("Edit Location");
    } else {
      openDialog(page);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        handleSearch={handleSearch}
        handleSearchKeyDown={handleSearchKeyDown}
        openDialog={handleOpenDialog}
        cartTotal={cartTotal}
        selectedStoreIds={selectedStoreIds}
        isUserDefinedList={isUserDefinedList}
        isAuthenticated={isAuthenticated}
        logout={logout}
      />
      {showCategoryBar && <CategoryBar />}
      <main className="flex-grow">
        <Suspense fallback={<LoadingSpinner fullScreen />}>{children}</Suspense>
      </main>
      <Footer />
      <SettingsDialog
        open={isDialogOpen}
        onOpenChange={(isOpen) => {
          if (!isOpen) closeDialog();
        }}
        defaultPage={dialogPage}
      />
      <Suspense fallback={null}>
        <Toaster />
      </Suspense>
      {showNextButton && (
        <NextButton className="fixed bottom-8 right-8 z-50 h-16 w-16 rounded-full shadow-lg" />
      )}
    </div>
  );
}
