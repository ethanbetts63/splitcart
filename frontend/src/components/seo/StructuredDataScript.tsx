/* Component registry: freetheplatform/frontend/registry/src/components/seo/StructuredDataScript.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
interface StructuredDataScriptProps {
  structuredData?: object | object[] | null;
}

/**
 * `JSON.stringify` escapes what JSON needs — quotes, backslashes, control
 * characters — but not `<`, because that is a perfectly legal character inside
 * a JSON string. This output is not going into a JSON file though: it goes
 * inside `<script>…</script>`, and the HTML parser does not parse JSON. It
 * scans for the literal characters `</script` and ends the element there.
 *
 * Everything that reaches this component is admin- or API-authored free text —
 * a bike description, a product name, an FAQ answer. A `</script>` anywhere in
 * one of those would close the tag early and hand whatever followed to the
 * browser as markup. `\u003c` is valid JSON, parses back to `<`, and can never
 * form that sequence.
 *
 * The replacement must be a literal backslash followed by `u003c`, so in this
 * source it is written with two: `'\\u003c'`. Written with one, `'\u003c'` is
 * simply the character `<`, and the replace becomes an identity no-op that
 * reads as correct and does nothing — the form this component shipped with
 * until 2026-09-20.
 */
function toJsonLd(structuredData: object | object[]): string {
  return JSON.stringify(structuredData).replace(/</g, '\\u003c');
}

const StructuredDataScript = ({ structuredData }: StructuredDataScriptProps) => {
  if (!structuredData || (Array.isArray(structuredData) && structuredData.length === 0)) {
    return null;
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: toJsonLd(structuredData) }}
    />
  );
};

export default StructuredDataScript;
