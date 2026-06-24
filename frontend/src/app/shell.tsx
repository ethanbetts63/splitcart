import { Suspense, type ReactNode } from "react";
import NavBar from "@/components/NavBar";
import Footer from "@/components/Footer";
import LoadingSpinner from "@/components/LoadingSpinner";
import { SettingsDialogWrapper } from "@/components/SettingsDialogWrapper";
import { FloatingNextButton } from "@/components/FloatingNextButton";
import { Toaster } from "@/components/ui/sonner";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      <main className="flex-grow">
        <Suspense fallback={<LoadingSpinner fullScreen />}>{children}</Suspense>
      </main>
      <Footer />
      <SettingsDialogWrapper />
      <Suspense fallback={null}>
        <Toaster />
      </Suspense>
      <FloatingNextButton />
    </div>
  );
}
