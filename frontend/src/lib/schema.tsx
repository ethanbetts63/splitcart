import type { JsonLdNode } from './seo';

interface StructuredDataScriptProps {
  structuredData?: JsonLdNode | JsonLdNode[] | null;
}

/**
 * The one place JSON-LD becomes a `<script>` tag — seo-standard.md section 3.
 *
 * SplitCart had four uncoordinated emission paths: `JsonLdScript` in this file,
 * a raw inline `<script>` on the homepage, a fifth-copy inline script inside
 * `FaqSection`, and `JsonLdItemList`, which built a script element in a
 * `useEffect` and appended it to `document.head` after hydration — so a crawler
 * reading the initial HTML never saw it at all. All four now route here, and
 * everything is server-rendered.
 *
 * None of the four escaped `<`. `JSON.stringify` escapes what JSON needs —
 * quotes, backslashes, control characters — but not `<`, because that is a
 * legal character inside a JSON string. This output is not going into a JSON
 * file though: it goes inside `<script>…</script>`, and the HTML parser does
 * not parse JSON. It scans for the literal characters `</script` and ends the
 * element there.
 *
 * Everything reaching this component is scraped or admin-authored free text — a
 * supermarket's product name, a brand, an FAQ answer. A `</script>` anywhere in
 * one of those would close the tag early and hand what followed to the browser
 * as markup. `\u003c` is valid JSON, parses back to `<`, and can never form
 * that sequence.
 *
 * The replacement must be a literal backslash followed by `u003c`, so in this
 * source it is written with two: `"\\u003c"`. Written with one, `"\u003c"` is
 * simply the character `<`, and the replace becomes an identity no-op that
 * reads as correct and does nothing.
 */
function toJsonLd(structuredData: JsonLdNode | JsonLdNode[]): string {
  return JSON.stringify(structuredData).replace(/</g, '\\u003c');
}

export default function StructuredDataScript({ structuredData }: StructuredDataScriptProps) {
  if (!structuredData || (Array.isArray(structuredData) && structuredData.length === 0)) {
    return null;
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: toJsonLd(structuredData) }}
    />
  );
}
