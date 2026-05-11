import HomePage from "@/page_components/HomePage";
import { createMetadata } from "@/lib/seo";
import type { Product } from "@/types";

export const revalidate = 600;

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

export const metadata = createMetadata({
  title: "SplitCart: Australian Grocery Price Comparison",
  description:
    "Every store has a deal, but finding them all takes forever. SplitCart compares prices across Coles, Woolworths, Aldi and IGA and splits your cart for the cheapest overall shop.",
  canonicalPath: "/",
});

export default async function Page() {
  const initialBargainProducts = await getInitialBargains();
  return <HomePage initialBargainProducts={initialBargainProducts} />;
}

async function getInitialBargains(): Promise<Product[]> {
  try {
    const response = await fetch(`${apiUrl}/api/products/bargain-carousel/?limit=20`, {
      next: { revalidate },
    });
    if (!response.ok) return [];
    return response.json();
  } catch {
    return [];
  }
}
