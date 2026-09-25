/**
 * Copied from `freethedesk/frontend/scripts/seo/ts-loader.mjs`. SplitCart is not
 * a component-registry consumer yet (`_docs/convergence/registry.md`), so this
 * is a local copy rather than a synced one. Unchanged from the original.
 *
 * Lets a build-time script `import()` the app's TypeScript modules directly,
 * so a check reads real values instead of scraping source text with regex.
 *
 * Node 22.6+ strips TypeScript types natively, and Node 23.6+ does it without
 * a flag — `lib/pages.ts` parses fine on its own. What it cannot do is resolve
 * the three things Next's bundler resolves for us:
 *
 *   1. Extensionless relative imports. `./suburbs` is not a module specifier
 *      Node ESM understands; `./suburbs.ts` is.
 *   2. The `@/` path alias from tsconfig.
 *   3. Asset imports (`.webp`, `.css`). There is nothing to load, and the
 *      value is never read by anything a check cares about, so they resolve
 *      to an empty module.
 *
 * `registerHooks` is synchronous and in-thread, so registering it and then
 * `await import(...)` in the same module works — no `--import` flag, no
 * loader thread, no dependency.
 *
 * Limitation: this strips types, it does not transpile. `.tsx` cannot be
 * loaded at all (`Unknown file extension ".tsx"`), so any check that needs to
 * see inside a page component still has to read it as text.
 *
 * Importing a module runs its top-level code. Every module a check loads must
 * therefore be free of side effects at import time — which the SEO registries
 * are, being plain data.
 */
import { registerHooks } from 'node:module';
import { existsSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve as resolvePath } from 'node:path';

const ASSET = /\.(webp|png|jpe?g|svg|avif|gif|ico|css)$/;
const EMPTY_MODULE = 'data:text/javascript,export default {}';

let registered = false;

/**
 * @param {string} srcDir Absolute path to the app's `src`, for the `@/` alias.
 */
export function registerTsLoader(srcDir) {
  if (registered) return;
  registered = true;

  registerHooks({
    resolve(specifier, context, next) {
      if (ASSET.test(specifier)) return { url: EMPTY_MODULE, shortCircuit: true };

      let spec = specifier;
      if (spec.startsWith('@/')) spec = pathToFileURL(resolvePath(srcDir, spec.slice(2))).href;

      if (spec.startsWith('.') || spec.startsWith('file:')) {
        const base = spec.startsWith('file:') ? spec : new URL(spec, context.parentURL).href;
        const path = fileURLToPath(base);
        for (const candidate of [path, `${path}.ts`, `${path}.mjs`, `${path}/index.ts`]) {
          if (existsSync(candidate))
            return { url: pathToFileURL(candidate).href, shortCircuit: true };
        }
      }

      return next(specifier, context);
    },
  });
}
