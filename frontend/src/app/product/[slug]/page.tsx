import ProductPage from "@/page_components/ProductPage";
import { noindexMetadata } from "@/lib/seo";
import { createBreadcrumbSchema, JsonLdScript } from "@/lib/schema";
import type { Product } from "@/types";

export const metadata = noindexMetadata;
export const revalidate = 1800;

type PageProps = { params: Promise<{ slug: string }> };

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

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
  const breadcrumbSchema = createBreadcrumbSchema([
    { name: "Home", path: "/" },
    { name: product?.name ?? "Product", path: `/product/${slug}` },
  ]);

  return (
    <>
      <JsonLdScript data={breadcrumbSchema} />
      <ProductPage product={product} slug={slug} />
    </>
  );
}
