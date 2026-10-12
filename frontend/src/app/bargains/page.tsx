import BargainsPage from '@/page_components/BargainsPage';
import {
  buildProductItemListSchema,
  buildRetailerSchemas,
  buildStaticPageGraph,
  companiesIn,
  metadataFor,
} from '@/lib/seo';
import StructuredDataScript from '@/components/seo/StructuredDataScript';
import { fetchCatalogue } from '@/lib/catalogue';
import type { PriceComparison, Product } from '@/types';

export const revalidate = 86400;

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
  return (await fetchCatalogue<PriceComparison[]>('/api/stats/bargains/', revalidate)) ?? [];
}

async function getCompanyProducts(): Promise<Record<string, Product[]>> {
  const companies = ['Coles', 'Woolworths', 'Aldi'];
  const entries = await Promise.all(
    companies.map(async (company) => {
      const params = new URLSearchParams({
        company_name: company,
        limit: '20',
      });
      const products = await fetchCatalogue<Product[]>(
        `/api/products/bargain-carousel/?${params.toString()}`,
        revalidate,
      );
      return [company, products ?? []] as const;
    }),
  );

  return Object.fromEntries(entries);
}
