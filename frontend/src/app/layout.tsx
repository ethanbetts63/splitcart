import type { Metadata } from 'next';
import '../index.css';
import { Analytics } from '@vercel/analytics/next';
import { SITE_NAME, SITE_URL } from '@/lib/siteConfig';
import { AppProviders } from './providers';
import { AppShell } from './shell';

export const metadata: Metadata = {
  // The origin is declared once, in `lib/siteConfig.ts`. This was the fourth
  // independent copy of it.
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_NAME,
    template: `%s | ${SITE_NAME}`,
  },
  description:
    'Compare grocery prices across Coles, Woolworths, and Aldi, then split your cart for the cheapest overall shop.',
  verification: {
    google: 'r5nGZauPlmuoFz7oRepvHlQq5AWr7zYuHrD_1jTSms8',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppProviders>
          <AppShell>{children}</AppShell>
        </AppProviders>
        <Analytics />
      </body>
    </html>
  );
}
