import BargainsPage from '@/page_components/BargainsPage';
import {
  buildProductItemListSchema,
  buildRetailerSchemas,
  buildStaticPageGraph,
  companiesIn,
  metadataFor,
} from '@/lib/seo';
import StructuredDataScript from '@/lib/schema';
import type { PriceComparison, Product } from '@/types';

export const revalidate = 86400;

const apiUrl = process.env.DJANGO_API_URL ?? 'http://localhost:8000';

export const metadata = metadataFor('/bargains');

export default async function Page() {
  const [initialBargainStats, initialCompanyProducts] = await Promise.all([
    getBargainStats(),
    getCompanyProducts(),
  ]);

  /**
   * One `ItemList` per company carousel, built server-side from the products
   * this page has already fetched, plus one canonical `Organization` node per
   * supermarket for the offers' `seller` to point at.
   */
  const allProducts = Object.values(initialCompanyProducts).flat();
  const itemLists = Object.entries(initialCompanyProducts)
    .map(([company, products]) =>
      buildProductItemListSchema(products, `Grocery bargains at ${company}`),
    )
    .filter((list) => list !== null);

  const graph = buildStaticPageGraph(
    '/bargains',
    itemLists.length ? [...itemLists, ...buildRetailerSchemas(companiesIn(allProducts))] : [],
  );

  return (
    <>
      <StructuredDataScript structuredData={graph} />
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
  const companies = ['Coles', 'Woolworths', 'Aldi'];
  const entries = await Promise.all(
    companies.map(async (company) => {
      try {
        const params = new URLSearchParams({
          company_name: company,
          limit: '20',
        });
        const response = await fetch(
          `${apiUrl}/api/products/bargain-carousel/?${params.toString()}`,
          { next: { revalidate } },
        );
        if (!response.ok) return [company, []] as const;
        return [company, await response.json()] as const;
      } catch {
        return [company, []] as const;
      }
    }),
  );

  return Object.fromEntries(entries);
}
