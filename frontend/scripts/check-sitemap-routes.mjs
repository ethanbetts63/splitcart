#!/usr/bin/env node
/** Thin entry point over `scripts/seo/sitemap-routes.mjs`. */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkSitemapRoutes } from './seo/sitemap-routes.mjs';

await checkSitemapRoutes({ root: join(dirname(fileURLToPath(import.meta.url)), '..') });
