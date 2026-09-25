import HomePage from "@/page_components/HomePage";
import {
  buildProductItemListSchema,
  buildRetailerSchemas,
  buildStaticPageGraph,
  companiesIn,
  metadataFor,
} from "@/lib/seo";
import StructuredDataScript from "@/lib/schema";
import type { Product } from "@/types";

export const revalidate = 600;

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

export const metadata = metadataFor("/");

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

  /**
   * The whole graph for this page in one document: the business entity every
   * other node points at, the site, this page, its trail, and the products the
   * bargain carousel shows.
   *
   * The `ItemList` is built here, server-side, from the products this page has
   * already fetched. It used to be assembled in a `useEffect` inside
   * `JsonLdItemList` and appended to `document.head` after hydration, which
   * means the initial HTML a crawler reads never contained it.
   */
  const itemList = buildProductItemListSchema(
    initialBargainProducts,
    "Grocery bargains across Coles, Woolworths and Aldi"
  );

  const graph = buildStaticPageGraph(
    "/",
    itemList
      ? [itemList, ...buildRetailerSchemas(companiesIn(initialBargainProducts))]
      : []
  );

  return (
    <>
      <StructuredDataScript structuredData={graph} />
      <HomePage initialBargainProducts={initialBargainProducts} />
    </>
  );
}
