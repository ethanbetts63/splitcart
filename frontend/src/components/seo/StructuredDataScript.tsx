/* Component registry: freetheplatform/frontend/registry/src/components/seo/StructuredDataScript.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
interface StructuredDataScriptProps {
  structuredData?: object | object[] | null;
}

/**
 * Escapes `<` as `\u003c` so admin- or API-authored text containing `</script>` cannot close the tag early.
 * The source needs two backslashes (`'\\u003c'`); with one the replace is a silent no-op.
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
