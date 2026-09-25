/* Component registry: freetheplatform/frontend/registry/src/types/FaqItem.ts
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */
/**
 * A link to render inside an FAQ answer. `phrase` must be text that already
 * appears in `answer` — the first non-overlapping, case-insensitive match
 * becomes the link. If the phrase is later edited out of the answer, the link
 * is silently dropped and the answer still renders.
 */
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
