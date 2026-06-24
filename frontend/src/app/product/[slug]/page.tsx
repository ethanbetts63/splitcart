import ProductPage from "@/page_components/ProductPage";
import { noindexMetadata } from "@/lib/seo";

export const metadata = noindexMetadata;

type PageProps = { params: Promise<{ slug: string }> };

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

async function getProduct(slug: string) {
  const productId = slug.split('-').pop();
  try {
    const res = await fetch(`${apiUrl}/api/products/${productId}/`, { cache: "no-store" });
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
