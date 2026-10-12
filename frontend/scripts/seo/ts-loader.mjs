/**
 * Lets a build-time script `import()` the app's TypeScript directly, so a check reads values, not source text.
 * Node strips types natively (22.6+; no flag from 23.6) but cannot resolve what Next's bundler does:
 *
 *   1. Extensionless relative imports (`./suburbs`).
 *   2. The `@/` alias from tsconfig.
 *   3. Asset imports (`.webp`, `.css`), which resolve to an empty module.
 *
 * `registerHooks` is synchronous and in-thread, so registering then `await import(...)` works with no flag or loader thread.
 *
 * Limits: types are stripped, not transpiled, so `.tsx` cannot load (read it as text). Imported modules run
 * their top-level code, so they must be side-effect free at import; the SEO registries are plain data.
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
