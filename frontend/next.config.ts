import { securityHeaders } from '@freetheplatform/web-security';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  images: {
    disableStaticImages: true,
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders({
          // Next's App Router inlines its own bootstrap, and Tailwind and
          // React's `style` prop both produce inline styles. The alternative
          // is a per-request nonce, which forces every page dynamic.
          allowInlineScripts: true,
          allowInlineStyles: true,

          hosts: {
            script: [
              // Vercel Analytics. On Vercel the tag is same-origin
              // (`/_vercel/insights/script.js`), but `next dev` loads
              // `script.debug.js` from here instead, and `headers()` applies in
              // development too — omit it and every local page load reports a
              // CSP refusal that does not exist in production.
              'https://va.vercel-scripts.com',
            ],
            img: [
              // Product photography, served straight from each chain's own CDN.
              // Nothing here goes through `next/image`: every tile renders a
              // plain <img> at the URL the API returns, so these origins are
              // what the browser actually requests. Miss one and that chain's
              // products render as broken images while the others are fine.
              //
              // Two of the three come from data — Woolworths from
              // `Company.image_url_template`, Aldi from `Product.aldi_image_url`
              // — so a chain changing CDN changes a database row and not this
              // file, and the first sign would be blocked images. Coles is
              // hard-coded in `ProductSerializer` instead. All three were read
              // off a real page load against the production API rather than off
              // the serializer, because the serializer is where they are
              // written, not proof of what is served.
              'https://cdn1.woolworths.media',
              'https://dm.apac.cms.aldi.cx',
              'https://productimages.coles.com.au',
            ],
            // No `connect` hosts: the browser calls only `/api/*` on its own origin,
            // which `proxy.ts` rewrites to Django, so `'self'` covers it.
          },
        }),
      },
      // No `/api/:path*` entry, and not an oversight — SEC §7's
      // `Cache-Control: no-store` cannot be delivered from here. `proxy.ts`
      // rewrites every `/api/*` path to another origin, and Next returns an
      // externally-rewritten response byte for byte: no `headers()` rule
      // survives it. Django's `NoCacheApiMiddleware` sets it instead.
      // Verified against `next start` — `curl -D -` on `/api/products/` shows
      // only Django's own headers, not one of the six above. A rule here would
      // look like the control and be inert.
      //
      // `_docs/convergence/security.md` carries what closing it actually
      // needs, and why a blanket `no-store` is the wrong shape for an API that
      // is mostly a public price catalogue.
    ];
  },
  async redirects() {
    return [
      {
        source: '/pillar-pages/eggs-and-dairy/',
        destination: '/categories/dairy-and-eggs',
        permanent: true,
      },
      {
        source: '/pillar-pages/eggs/',
        destination: '/categories/dairy-and-eggs',
        permanent: true,
      },
      {
        source: '/pillar-pages/pet-and-baby/',
        destination: '/categories/baby',
        permanent: true,
      },
      {
        source: '/pillar-pages/fruit-veg-and-spices/',
        destination: '/categories/fruit-and-veg',
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
