import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import PillarPage from '@/page_components/PillarPage';
import {
  buildBreadcrumbSchema,
  buildGraph,
  buildMetadata,
  buildOrganizationSchema,
  buildProductItemListSchema,
  buildRetailerSchemas,
  buildWebPageSchema,
  buildWebSiteSchema,
  companiesIn,
} from '@/lib/seo';
import StructuredDataScript from '@/components/seo/StructuredDataScript';
import { CATEGORY_PAGE_UPDATED } from '@/lib/pages';
import type { PillarPage as PillarPageType, Product } from '@/types';
import { CATEGORY_SLUGS, type CategorySlug } from '@/data/categories';
import { fetchCatalogue } from '@/lib/catalogue';

type PageProps = {
  params: Promise<{ slug: string }>;
};

const FALLBACK_TITLE = 'Category';
const FALLBACK_DESCRIPTION = 'Compare supermarket prices by grocery category with SplitCart.';

export function generateStaticParams() {
  return CATEGORY_SLUGS.map((slug) => ({ slug }));
}

export const revalidate = 86400;

async function getPillarPage(slug: string): Promise<PillarPageType | null> {
  return fetchCatalogue<PillarPageType>(`/api/pillar-pages/${slug}/`, revalidate);
}

/**
 * These pages are a dynamic family, not registry entries: their title and
 * description come from the Django pillar-page record, which a literal string
 * in `lib/pages.ts` could not hold. What the registry does own is the
 * `lastmod`/`dateModified` date, because no date exists on the record itself.
 */
function updatedFor(slug: string): string | undefined {
  return CATEGORY_PAGE_UPDATED[slug as CategorySlug];
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const pillarPage = await getPillarPage(slug);

  return buildMetadata({
    path: `/categories/${slug}`,
    title: pillarPage?.hero_title ?? FALLBACK_TITLE,
    description: pillarPage?.introduction_paragraph ?? FALLBACK_DESCRIPTION,
  });
}

async function getCategoryProducts(slugs: string[]): Promise<Record<string, Product[]>> {
  const entries = await Promise.all(
    slugs.map(async (categorySlug) => {
      const params = new URLSearchParams({
        primary_category_slugs: categorySlug,
        limit: '20',
        ordering: 'carousel_default',
      });
      const data = await fetchCatalogue<{ results?: Product[] }>(
        `/api/products/?${params.toString()}`,
        revalidate,
      );
      return [categorySlug, data?.results ?? []] as const;
    }),
  );
  return Object.fromEntries(entries);
}

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const pillarPage = await getPillarPage(slug);

  if (!pillarPage) notFound();

  const categorySlugs = pillarPage.primary_categories.map((c) => c.slug);
  const categoryProducts = await getCategoryProducts(categorySlugs);

  const path = `/categories/${slug}`;
  const title = pillarPage.hero_title ?? FALLBACK_TITLE;
  const description = pillarPage.introduction_paragraph ?? FALLBACK_DESCRIPTION;

  const allProducts = Object.values(categoryProducts).flat();
  const itemLists = Object.entries(categoryProducts)
    .map(([categorySlug, products]) =>
      buildProductItemListSchema(products, `${title}: ${categorySlug}`),
    )
    .filter((list) => list !== null);

  const graph = buildGraph([
    buildOrganizationSchema(),
    buildWebSiteSchema(),
    buildWebPageSchema({
      path,
      name: title,
      description,
      updated: updatedFor(slug),
    }),
    buildBreadcrumbSchema(
      [
        { name: 'Home', path: '/' },
        { name: title, path },
      ],
      path,
    ),
    ...(itemLists.length ? [...itemLists, ...buildRetailerSchemas(companiesIn(allProducts))] : []),
  ]);

  return (
    <>
      <StructuredDataScript structuredData={graph} />
      <PillarPage pillarPage={pillarPage} slug={slug} categoryProducts={categoryProducts} />
    </>
  );
}
