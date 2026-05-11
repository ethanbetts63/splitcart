import ProductPage from "@/page_components/ProductPage";
import { noindexMetadata } from "@/lib/seo";

export const metadata = noindexMetadata;

export default function Page() {
  return <ProductPage />;
}
