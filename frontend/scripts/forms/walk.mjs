/**
 * Shared source-tree walk for the forms checks. One skip list, one traversal
 * convention — the two engines used to carry byte-identical private copies of
 * this, which is the same drift-by-copy the registry exists to prevent.
 */
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const SKIP_DIRECTORIES = new Set(['node_modules', '.next', 'dist', 'build']);

/** Every file under `directory` whose name ends with one of `extensions`. */
export function walk(directory, extensions, out = []) {
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) {
      if (!SKIP_DIRECTORIES.has(entry)) walk(path, extensions, out);
    } else if (extensions.some((extension) => entry.endsWith(extension))) {
      out.push(path);
    }
  }
  return out;
}
