import type { Metadata } from "next";
import { notFound } from "next/navigation";
import PillarPage from "@/page_components/PillarPage";
import { createMetadata } from "@/lib/seo";
import type { PillarPage as PillarPageType } from "@/types";

type PageProps = {
  params: Promise<{ slug: string }>;
};

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

const KNOWN_SLUGS = [
  "snacks-and-sweets",
  "meat-and-seafood",
  "dairy-and-eggs",
  "fruit-and-veg",
  "pantry",
  "international-herbs-and-spices",
  "bakery-and-deli",
  "drinks",
  "health-beauty-and-supplements",
  "home-cleaning-gardening-and-pets",
  "baby",
];

export function generateStaticParams() {
  return KNOWN_SLUGS.map((slug) => ({ slug }));
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

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const pillarPage = await getPillarPage(slug);

  if (!pillarPage) notFound();

  return <PillarPage pillarPage={pillarPage} slug={slug} />;
}
