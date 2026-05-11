import HomePage from "@/page_components/HomePage";
import { createMetadata } from "@/lib/seo";

export const revalidate = 600;

export const metadata = createMetadata({
  title: "SplitCart: Australian Grocery Price Comparison",
  description:
    "Every store has a deal, but finding them all takes forever. SplitCart compares prices across Coles, Woolworths, Aldi and IGA and splits your cart for the cheapest overall shop.",
  canonicalPath: "/",
});

export default function Page() {
  return <HomePage />;
}
