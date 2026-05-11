import type { Metadata } from "next";
import PillarPage from "@/page_components/PillarPage";
import { createMetadata } from "@/lib/seo";
import type { PillarPage as PillarPageType, Product } from "@/types";

type PageProps = {
  params: Promise<{ slug: string }>;
};

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

async function getPillarPage(slug: string): Promise<PillarPageType | null> {
  try {
    const response = await fetch(`${apiUrl}/api/pillar-pages/${slug}/`, {
      next: { revalidate: 60 * 60 * 24 },
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

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const initialPillarPage = await getPillarPage(slug);
  const initialCarouselProducts = initialPillarPage
    ? await getInitialCarouselProducts(initialPillarPage)
    : {};

  return (
    <PillarPage
      initialPillarPage={initialPillarPage}
      initialCarouselProducts={initialCarouselProducts}
    />
  );
}

async function getInitialCarouselProducts(
  pillarPage: PillarPageType
): Promise<Record<string, Product[]>> {
  const entries = await Promise.all(
    pillarPage.primary_categories.map(async (category) => {
      try {
        const params = new URLSearchParams({
          primary_category_slugs: category.slug,
          ordering: "carousel_default",
          limit: "20",
        });
        const response = await fetch(`${apiUrl}/api/products/?${params.toString()}`, {
          next: { revalidate: 60 * 10 },
        });
        if (!response.ok) return [category.slug, []] as const;
        const data = await response.json();
        const products = Array.isArray(data) ? data : data.results ?? [];
        return [category.slug, products] as const;
      } catch {
        return [category.slug, []] as const;
      }
    })
  );

  return Object.fromEntries(entries);
}
