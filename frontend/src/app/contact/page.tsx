import ContactPage from '@/page_components/ContactPage';
import { buildStaticPageGraph, metadataFor } from '@/lib/seo';
import StructuredDataScript from '@/components/seo/StructuredDataScript';

export const metadata = metadataFor('/contact');

/**
 * `ContactPage` is a `WebPage` subtype, so it replaces the generic `WebPage`
 * node rather than sitting alongside a second copy of it.
 *
 * The `ContactPoint` itself moved onto the `Organization` node in `lib/seo.ts`,
 * where schema.org defines it and where the rest of the graph can reference it.
 * This page used to mint its own — a `ContactPage` with an inline
 * `contactPoint` and a `mainEntityOfPage` pointing at a bare URL string instead
 * of an `@id`, so nothing in the graph joined up.
 */
export default function Page() {
  return (
    <>
      <StructuredDataScript structuredData={buildStaticPageGraph('/contact', [], 'ContactPage')} />
      <ContactPage />
    </>
  );
}
