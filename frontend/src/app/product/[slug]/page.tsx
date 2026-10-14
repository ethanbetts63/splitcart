import type { Metadata } from 'next';
import { notFound, permanentRedirect } from 'next/navigation';

import ProductPage from '@/page_components/ProductPage';
import StructuredDataScript from '@/components/seo/StructuredDataScript';
import { fetchCatalogue } from '@/lib/catalogue';
import { productDescription, productLabel, productTitle } from '@/lib/productPage';
import {
  absoluteUrl,
  buildBreadcrumbSchema,
  buildGraph,
  buildMetadata,
  buildOrganizationSchema,
  buildProductSchema,
  buildRetailerSchemas,
  buildWebPageSchema,
  buildWebSiteSchema,
  companiesIn,
  webPageId,
} from '@/lib/seo';
import type { Product } from '@/types';

/**
 * Product pages are a conditional family (`DYNAMIC_ROUTE_FAMILIES` in
 * `lib/pages.ts`): each one is indexable or `noindex` by `product.indexable`,
 * which Django decides in `products/utils/indexable.py` — at least two of Aldi,
 * Coles and Woolworths with a current price. The sitemap lists exactly that
 * set, from the same rule.
 *
 * They were robots-disallowed until 2026-10-14, on the grounds that every
 * crawl was a live fetch against one small Django instance. What bounds that
 * load is this revalidation window: a page is fetched from Django at most once
 * a day however often it is crawled, and prices only change when a scrape is
 * ingested. A crawler must be able to fetch a page to read its `noindex`, so a
 * disallow and a per-page decision cannot coexist.
 */
export const revalidate = 86400;

/**
 * None at build time — there are tens of thousands — but declaring the family
 * static is what makes each page cached on first request and served from that
 * cache for `revalidate`, rather than rendered per request.
 */
export function generateStaticParams(): { slug: string }[] {
  return [];
}

type PageProps = { params: Promise<{ slug: string }> };

async function getProduct(slug: string): Promise<Product | null> {
  const productId = slug.split('-').pop();
  if (!productId || !/^\d+$/.test(productId)) return null;
  return fetchCatalogue<Product>(`/api/products/${productId}/`, revalidate);
}

function pathFor(product: Product): string {
  return `/product/${product.slug}`;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  return buildMetadata({
    path: pathFor(product),
    title: productTitle(product),
    description: productDescription(product),
    noindex: !product.indexable,
  });
}

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  // Only the id in a slug is read, so every spelling of the name resolves.
  // One of them is the page; the rest send it there.
  if (product.slug && slug !== product.slug) permanentRedirect(pathFor(product));

  const path = pathFor(product);
  const productNode = product.indexable ? buildProductSchema(product, absoluteUrl(path)) : null;

  return (
    <>
      {productNode && (
        <StructuredDataScript
          structuredData={buildGraph([
            buildOrganizationSchema(),
            buildWebSiteSchema(),
            {
              ...buildWebPageSchema({
                path,
                name: productTitle(product),
                description: productDescription(product),
                type: 'ItemPage',
              }),
              mainEntity: { '@id': `${webPageId(path)}-product` },
            },
            buildBreadcrumbSchema(
              [
                { name: 'Home', path: '/' },
                { name: productLabel(product), path },
              ],
              path,
            ),
            { ...productNode, '@id': `${webPageId(path)}-product` },
            ...buildRetailerSchemas(companiesIn([product])),
          ])}
        />
      )}
      <ProductPage product={product} />
    </>
  );
}
