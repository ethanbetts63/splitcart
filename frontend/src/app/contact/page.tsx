import ContactPage from "@/page_components/ContactPage";
import { createMetadata } from "@/lib/seo";

export const metadata = createMetadata({
  title: "Contact Us",
  description:
    "Have questions, suggestions, or feedback? Get in touch with SplitCart.",
  canonicalPath: "/contact",
});

export default function Page() {
  return <ContactPage />;
}
