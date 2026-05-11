import type { Metadata } from "next";
import "../index.css";
import "../css/CategoryCarousel.css";
import "leaflet/dist/leaflet.css";
import { Analytics } from "@vercel/analytics/next";
import { AppProviders } from "./providers";
import { AppShell } from "./shell";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.splitcart.com.au"),
  title: {
    default: "SplitCart",
    template: "%s | SplitCart",
  },
  description:
    "Compare grocery prices across Coles, Woolworths, Aldi and IGA, then split your cart for the cheapest overall shop.",
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
