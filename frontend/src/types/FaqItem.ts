/* Component registry: freetheplatform/frontend/registry/src/types/FaqItem.ts
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
/** A link inside an FAQ answer: the first non-overlapping, case-insensitive match of `phrase` in `answer`. Dropped silently if the phrase is edited out. */
interface FaqLink {
  phrase: string;
  href: string;
}

export interface FaqItem {
  question: string;
  /** Plain text — the source of `FAQPage` structured data, which must not contain markup. */
  answer: string;
  links?: FaqLink[];
}
