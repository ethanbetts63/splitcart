import ContactPage from "@/page_components/ContactPage";
import { createMetadata } from "@/lib/seo";

export const metadata = createMetadata({
  title: "Contact Us",
  description:
    "Have questions, suggestions, or feedback? Get in touch with SplitCart.",
  canonicalPath: "/contact",
});

const contactPageSchema = {
  "@context": "https://schema.org",
  "@type": "ContactPage",
  name: "Contact Us",
  description: "Have questions, suggestions, or feedback? Get in touch with us.",
  url: "https://www.splitcart.com.au/contact",
  mainEntityOfPage: {
    "@type": "WebPage",
    "@id": "https://www.splitcart.com.au/contact",
  },
  contactPoint: {
    "@type": "ContactPoint",
    email: "ethanbetts63@gmail.com",
    contactType: "Customer Support",
    availableLanguage: "English",
  },
};

export default function Page() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(contactPageSchema) }}
      />
      <ContactPage />
    </>
  );
}
