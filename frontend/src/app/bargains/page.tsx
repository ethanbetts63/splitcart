import BargainsPage from "@/page_components/BargainsPage";
import { createMetadata } from "@/lib/seo";
import type { PriceComparison, Product } from "@/types";

export const revalidate = 86400;

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

export const metadata = createMetadata({
  title: "SplitCart: Australia's Best Grocery Bargains",
  description:
    "Find the best grocery bargains in Australia. SplitCart compares prices across Coles, Woolworths, Aldi, and IGA to find you the biggest discounts.",
  canonicalPath: "/bargains",
});

const webPageSchema = {
  "@context": "https://schema.org",
  "@type": "WebPage",
  name: "SplitCart: Australia's Best Grocery Bargains",
  description:
    "Find the best grocery bargains in Australia. SplitCart compares prices across Coles, Woolworths, Aldi, and IGA to find you the biggest discounts.",
  url: "https://www.splitcart.com.au/bargains",
};

export default async function Page() {
  const [initialBargainStats, initialCompanyProducts] = await Promise.all([
    getBargainStats(),
    getCompanyProducts(),
  ]);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(webPageSchema) }}
      />
      <BargainsPage
        initialBargainStats={initialBargainStats}
        initialCompanyProducts={initialCompanyProducts}
      />
    </>
  );
}

async function getBargainStats(): Promise<PriceComparison[]> {
  try {
    const response = await fetch(`${apiUrl}/api/stats/bargains/`, {
      next: { revalidate },
    });
    if (!response.ok) return [];
    return response.json();
  } catch {
    return [];
  }
}

async function getCompanyProducts(): Promise<Record<string, Product[]>> {
  const companies = ["Coles", "Woolworths", "Aldi", "Iga"];
  const entries = await Promise.all(
    companies.map(async (company) => {
      try {
        const params = new URLSearchParams({
          company_name: company,
          limit: "20",
        });
        const response = await fetch(
          `${apiUrl}/api/products/bargain-carousel/?${params.toString()}`,
          { next: { revalidate } }
        );
        if (!response.ok) return [company, []] as const;
        return [company, await response.json()] as const;
      } catch {
        return [company, []] as const;
      }
    })
  );

  return Object.fromEntries(entries);
}
