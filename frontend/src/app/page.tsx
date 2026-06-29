import HomePage from "@/page_components/HomePage";
import { createMetadata } from "@/lib/seo";
import type { Product } from "@/types";

export const revalidate = 600;

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

export const metadata = createMetadata({
  title: "SplitCart: Australian Grocery Price Comparison",
  description:
    "Every store has a deal, but finding them all takes forever. SplitCart compares prices across Coles, Woolworths, and Aldi and splits your cart for the cheapest overall shop.",
  canonicalPath: "/",
});

const webSiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "SplitCart",
  url: "https://www.splitcart.com.au",
  founder: { "@type": "Person", name: "Ethan Betts" },
  potentialAction: {
    "@type": "SearchAction",
    target: {
      "@type": "EntryPoint",
      urlTemplate: "https://www.splitcart.com.au/search?q={search_term_string}",
    },
    "query-input": "required name=search_term_string",
  },
};

async function getBargainProducts(): Promise<Product[]> {
  try {
    const params = new URLSearchParams({ limit: "20" });
    const response = await fetch(
      `${apiUrl}/api/products/bargain-carousel/?${params.toString()}`,
      { next: { revalidate } }
    );
    if (!response.ok) return [];
    return response.json();
  } catch {
    return [];
  }
}

export default async function Page() {
  const initialBargainProducts = await getBargainProducts();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(webSiteSchema) }}
      />
      <HomePage initialBargainProducts={initialBargainProducts} />
    </>
  );
}
