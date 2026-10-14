import { Suspense, type ReactNode } from 'react';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import { SettingsDialogWrapper } from '@/components/SettingsDialogWrapper';
import { FloatingNextButton } from '@/components/FloatingNextButton';
import { Toaster } from '@/components/common/sonner';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      {/*
        No Suspense boundary around the page. One used to sit here, and it made
        every page stream: the 200 and the loading message went out before the
        page had run, so a notFound() answered 200 with a 404 body and a
        permanentRedirect() never reached the status line. A page that needs a
        boundary (search, for useSearchParams) declares its own.
      */}
      <main className="flex-grow">{children}</main>
      <Footer />
      <SettingsDialogWrapper />
      <Suspense fallback={null}>
        <Toaster />
      </Suspense>
      <FloatingNextButton />
    </div>
  );
}
