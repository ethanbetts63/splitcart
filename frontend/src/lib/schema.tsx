/**
 * Forwarder. The component moved to `@/components/seo/StructuredDataScript`,
 * which is the component registry's path for it and now holds a byte-identical
 * registry copy (`_docs/convergence/registry.md`, RG-2).
 *
 * This file stays only because five route files still import `@/lib/schema`,
 * and it is one line rather than a second implementation: there is still
 * exactly one emitter, which is the whole point of the thing it forwards to.
 * Delete it in the commit that repoints `app/page.tsx`, `app/bargains/page.tsx`,
 * `app/categories/[slug]/page.tsx`, `app/contact/page.tsx` and
 * `app/privacy/page.tsx`.
 *
 * What the registry component is for, kept here because it is the reason the
 * adoption was worth doing: SplitCart had four uncoordinated JSON-LD emission
 * paths and not one of them escaped `<`. `JSON.stringify` escapes what JSON
 * needs — quotes, backslashes, control characters — but `<` is legal inside a
 * JSON string, and this output goes inside `<script>…</script>`, where the HTML
 * parser scans for the literal characters `</script` and ends the element
 * there. Everything reaching it is scraped or admin-authored free text: a
 * supermarket's product name, a brand, an FAQ answer.
 */
export { default } from '@/components/seo/StructuredDataScript';
