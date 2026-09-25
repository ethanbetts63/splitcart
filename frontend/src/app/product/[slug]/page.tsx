import ProductPage from '@/page_components/ProductPage';
import type { Product } from '@/types';

/**
 * Product pages are state 4 — robots-disallowed — and nothing else.
 *
 * They are an unbounded generated surface: one page per product, each served by
 * a live fetch against the Django API. `/product` is in `DISALLOWED_ROUTES` in
 * `app/robots.txt/route.ts`, which is the single declaration of that decision.
 *
 * There is deliberately no `noindex` metadata and no structured data here any
 * more. Both were inert: a disallowed page is never fetched, so the robots meta
 * on it is never read and the JSON-LD on it is never parsed. seo-standard.md
 * section 2 forbids declaring both states, and a route carrying an assertion
 * nothing can act on reads as protection that is not there. If `/product` is
 * ever removed from the disallow list, this page needs a real indexation
 * decision made at that point — not a leftover one.
 */

export const revalidate = 1800;

type PageProps = { params: Promise<{ slug: string }> };

const apiUrl = process.env.DJANGO_API_URL ?? 'http://localhost:8000';

async function getProduct(slug: string): Promise<Product | null> {
  const productId = slug.split('-').pop();
  try {
    const res = await fetch(`${apiUrl}/api/products/${productId}/`, {
      next: { revalidate },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const product = await getProduct(slug);

  return <ProductPage product={product} slug={slug} />;
}
