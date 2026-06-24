import HomePage from "@/page_components/HomePage";
import { createMetadata } from "@/lib/seo";

export const revalidate = 600;

export const metadata = createMetadata({
  title: "SplitCart: Australian Grocery Price Comparison",
  description:
    "Every store has a deal, but finding them all takes forever. SplitCart compares prices across Coles, Woolworths, Aldi and IGA and splits your cart for the cheapest overall shop.",
  canonicalPath: "/",
});

const webSiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "SplitCart",
  url: "https://www.splitcart.com.au",
  founder: { "@type": "Person", name: "Ethan Betts" },
  potentialAction: {
    "@type": "SearchAction",
    target: {
      "@type": "EntryPoint",
      urlTemplate: "https://www.splitcart.com.au/search?q={search_term_string}",
    },
    "query-input": "required name=search_term_string",
  },
};

export default function Page() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(webSiteSchema) }}
      />
      <HomePage />
    </>
  );
}
