/* Component registry: freetheplatform/frontend/registry/src/components/seo/StructuredDataScript.tsx
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
interface StructuredDataScriptProps {
  structuredData?: object | readonly object[] | null;
}

/**
 * The nodes to emit, as one flat list. A builder that returns a list, placed in a page's list
 * unspread, nests an array inside the array; Google reads the nested one as an "invalid top level
 * element" and drops every node in it (allbikes' SYM parts pages, 2026-10). The type cannot catch
 * it, since `object` absorbs `object[]`, so it is flattened here, where every page passes.
 */
function toNodes(structuredData: object | readonly object[]): object[] {
  return [structuredData].flat(Infinity).filter(Boolean) as object[];
}

/**
 * Escapes `<` as `<` so admin- or API-authored text containing `</script>` cannot close the tag early.
 * The source needs two backslashes (`'\\u003c'`); with one the replace is a silent no-op.
 */
function toJsonLd(nodes: object[]): string {
  return JSON.stringify(nodes.length === 1 ? nodes[0] : nodes).replace(/</g, '\\u003c');
}

const StructuredDataScript = ({ structuredData }: StructuredDataScriptProps) => {
  const nodes = structuredData ? toNodes(structuredData) : [];
  if (nodes.length === 0) return null;

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: toJsonLd(nodes) }} />
  );
};

export default StructuredDataScript;
