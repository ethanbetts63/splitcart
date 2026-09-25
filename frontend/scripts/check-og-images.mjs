#!/usr/bin/env node
/**
 * Thin entry point over `scripts/seo/og-images.mjs`. Only the file list is
 * repo-specific.
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkOgImages } from './seo/og-images.mjs';

checkOgImages({
  root: join(dirname(fileURLToPath(import.meta.url)), '..'),
  sources: ['src/lib/seo.ts'],
});
