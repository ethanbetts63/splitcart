#!/usr/bin/env node
/**
 * Regenerates `src/lib/text-sizes.generated.ts` from tokens.css, or with
 * `--check` fails when it is stale. The work lives in freetheplatform's
 * shared lint directory; this file only says where splitcart keeps its files.
 */
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { syncTextScale } from '../../../freetheplatform/frontend/lint/text-scale.mjs';

const { ok, message } = syncTextScale({
  root: join(dirname(fileURLToPath(import.meta.url)), '..'),
  tokensPath: 'src/styles/tokens.css',
  modulePath: 'src/lib/text-sizes.generated.ts',
  syncCommand: 'npm run tokens:text-scale',
  check: process.argv.includes('--check'),
});

if (!ok) {
  console.error(`\ncheck-text-scale failed:\n\n• ${message}\n`);
  process.exit(1);
}
console.log(`text-scale: ${message}`);
