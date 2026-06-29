import type { Metadata } from "next";
import { notFound } from "next/navigation";
import PillarPage from "@/page_components/PillarPage";
import { createMetadata } from "@/lib/seo";
import { createBreadcrumbSchema, JsonLdScript } from "@/lib/schema";
import type { PillarPage as PillarPageType, Product } from "@/types";
import { CATEGORY_SLUGS } from "@/data/categories";

type PageProps = {
  params: Promise<{ slug: string }>;
};

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

export function generateStaticParams() {
  return CATEGORY_SLUGS.map((slug) => ({ slug }));
}

export const revalidate = 86400;

async function getPillarPage(slug: string): Promise<PillarPageType | null> {
  try {
    const response = await fetch(`${apiUrl}/api/pillar-pages/${slug}/`, {
      next: { revalidate },
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const pillarPage = await getPillarPage(slug);

  if (!pillarPage) {
    return createMetadata({
      title: "Category",
      description: "Compare supermarket prices by grocery category with SplitCart.",
      canonicalPath: `/categories/${slug}`,
    });
  }

  return createMetadata({
    title: pillarPage.hero_title ?? "Category",
    description:
      pillarPage.introduction_paragraph ??
      "Compare supermarket prices by grocery category with SplitCart.",
    canonicalPath: `/categories/${slug}`,
  });
}

async function getCategoryProducts(slugs: string[]): Promise<Record<string, Product[]>> {
  const entries = await Promise.all(
    slugs.map(async (categorySlug) => {
      try {
        const params = new URLSearchParams({
          primary_category_slugs: categorySlug,
          limit: "20",
          ordering: "carousel_default",
        });
        const response = await fetch(`${apiUrl}/api/products/?${params.toString()}`, {
          next: { revalidate },
        });
        if (!response.ok) return [categorySlug, []] as const;
        const data = await response.json();
        return [categorySlug, data.results ?? []] as const;
      } catch {
        return [categorySlug, []] as const;
      }
    })
  );
  return Object.fromEntries(entries);
}

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const pillarPage = await getPillarPage(slug);

  if (!pillarPage) notFound();

  const categorySlugs = pillarPage.primary_categories.map((c) => c.slug);
  const categoryProducts = await getCategoryProducts(categorySlugs);

  const title = pillarPage.hero_title ?? "Category";
  const breadcrumbSchema = createBreadcrumbSchema([
    { name: "Home", path: "/" },
    { name: title, path: `/categories/${slug}` },
  ]);

  return (
    <>
      <JsonLdScript data={breadcrumbSchema} />
      <PillarPage pillarPage={pillarPage} slug={slug} categoryProducts={categoryProducts} />
    </>
  );
}
