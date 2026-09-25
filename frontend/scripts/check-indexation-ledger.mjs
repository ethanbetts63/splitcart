#!/usr/bin/env node
/**
 * Thin entry point over `scripts/seo/indexation-ledger.mjs`. Only the two
 * values below are repo-specific, because how a page declares noindex differs
 * by how each app builds its metadata.
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkIndexationLedger } from './seo/indexation-ledger.mjs';

await checkIndexationLedger({
  root: join(dirname(fileURLToPath(import.meta.url)), '..'),
  noindexIn: /NOINDEX_METADATA/,
  noindexFix: 'Give the page `export const metadata = NOINDEX_METADATA;` from `@/lib/pages`.',
});
