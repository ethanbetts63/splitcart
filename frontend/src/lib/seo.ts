import type { Metadata } from "next";

import type { Product } from "@/types/Product";
import {
  breadcrumbItemsFor,
  STATIC_PAGES,
  type PagePath,
  type StaticPage,
} from "./pages";
import {
  CONTACT_EMAIL,
  DEFAULT_OG_HEIGHT,
  DEFAULT_OG_IMAGE,
  DEFAULT_OG_WIDTH,
  ORGANIZATION_ID,
  ORGANIZATION_LOGO,
  SITE_NAME,
  SITE_URL,
  WEBSITE_ID,
} from "./siteConfig";

/**
 * Metadata and structured data for SplitCart.
 *
 * Three things live here and nowhere else: the one URL-spelling helper, the one
 * metadata builder, and the `build*Schema` family that produces the `@id` graph
 * (seo-standard.md sections 3 and 5). The origin itself is in the leaf
 * `lib/siteConfig.ts`, and the page facts are in `lib/pages.ts`.
 *
 * Nothing in here reaches a request context or the API client, so it stays
 * importable from a statically-rendered route.
 */

/** A JSON-LD node. Loose by necessity — schema.org is not a closed vocabulary. */
export type JsonLdNode = Record<string, unknown>;

/**
 * One URL spelling per route, shared by the canonical tag, the OG url, the
 * sitemap and every `@id`. The homepage is `{SITE_URL}/` with the trailing
 * slash in all of them, because the question is answered here once instead of
 * separately in each caller — which is how the sitemap came to advertise
 * `/categories/baby/` while the page's own canonical said `/categories/baby`.
 */
export function absoluteUrl(path: string): string {
  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

interface MetadataOptions {
  path: string;
  title: string;
  description: string;
  /** Skip the `%s | SplitCart` template for a title that already says it. */
  absoluteTitle?: boolean;
  noindex?: boolean;
}

export function buildMetadata({
  path,
  title,
  description,
  absoluteTitle = false,
  noindex = false,
}: MetadataOptions): Metadata {
  const canonical = absoluteUrl(path);

  return {
    title: absoluteTitle ? { absolute: title } : title,
    description,
    alternates: { canonical },
    robots: noindex ? { index: false, follow: false } : undefined,
    openGraph: {
      title,
      description,
      url: canonical,
      siteName: SITE_NAME,
      type: "website",
      locale: "en_AU",
      images: [
        {
          url: DEFAULT_OG_IMAGE,
          width: DEFAULT_OG_WIDTH,
          height: DEFAULT_OG_HEIGHT,
          alt: `${SITE_NAME} — Australian grocery price comparison`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [DEFAULT_OG_IMAGE],
    },
  };
}

/** Metadata for a route that is one record in `STATIC_PAGES`. */
export function metadataFor(path: PagePath): Metadata {
  const page: StaticPage = STATIC_PAGES[path];
  return buildMetadata({ ...page, path });
}

/* ------------------------------------------------------------------ *
 * The @id graph — seo-standard.md section 3.
 *
 * One business entity at a stable @id; every other node references it with
 * `{ "@id": … }` instead of minting a second copy of it. Before this, no node
 * anywhere in the repo carried an @id at all, SplitCart itself never appeared
 * as a schema subject, and each product offer minted a fresh anonymous
 * `Organization` for Coles or Woolworths.
 * ------------------------------------------------------------------ */

/** Wrap top-level nodes as one document. `@graph` is what lets the @ids link. */
export function buildGraph(nodes: JsonLdNode[]): JsonLdNode {
  return { "@context": "https://schema.org", "@graph": nodes };
}

/**
 * SplitCart itself. `Organization` rather than a `LocalBusiness` subtype —
 * there is no premises, no opening hours and no service area beyond "the
 * Australian supermarkets we have data for", and claiming a local business is
 * claiming a fact that is not true.
 *
 * `founder` is an `Organization` property (schema.org: domainIncludes
 * Organization, rangeIncludes Organization or Person). It was previously
 * stapled to the homepage's `WebSite` node, where schema.org does not define
 * it — an invented property on the wrong type, which is dropped silently.
 */
export function buildOrganizationSchema(): JsonLdNode {
  return {
    "@type": "Organization",
    "@id": ORGANIZATION_ID,
    name: SITE_NAME,
    url: absoluteUrl("/"),
    logo: absoluteUrl(ORGANIZATION_LOGO),
    email: CONTACT_EMAIL,
    description:
      "SplitCart compares grocery prices across Coles, Woolworths and Aldi and finds the cheapest way to split a shopping list across them.",
    founder: { "@type": "Person", name: "Ethan Betts" },
    areaServed: { "@type": "Country", name: "Australia" },
    contactPoint: {
      "@type": "ContactPoint",
      email: CONTACT_EMAIL,
      contactType: "customer support",
      availableLanguage: "English",
    },
  };
}

/**
 * The site.
 *
 * No `SearchAction`/sitelinks searchbox: Google removed that feature from
 * Search in October 2024 and archived its documentation, so the markup claims
 * an outcome that no longer exists. `/search` is robots-disallowed here
 * besides, which made the promised endpoint one no crawler may fetch.
 */
export function buildWebSiteSchema(): JsonLdNode {
  return {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    name: SITE_NAME,
    url: absoluteUrl("/"),
    inLanguage: "en-AU",
    publisher: { "@id": ORGANIZATION_ID },
  };
}

export function webPageId(path: string): string {
  return `${absoluteUrl(path)}#webpage`;
}

export function breadcrumbId(path: string): string {
  return `${absoluteUrl(path)}#breadcrumb`;
}

interface WebPageOptions {
  path: string;
  name: string;
  description: string;
  /**
   * ISO date from the registry, or from a date the underlying record genuinely
   * carries. Never invented, and never the build time.
   */
  updated?: string;
  /** A more specific `WebPage` subtype, e.g. `ContactPage`. */
  type?: string;
  /** Emitted only when a `BreadcrumbList` with the matching @id is also in the graph. */
  hasBreadcrumb?: boolean;
}

export function buildWebPageSchema({
  path,
  name,
  description,
  updated,
  type = "WebPage",
  hasBreadcrumb = true,
}: WebPageOptions): JsonLdNode {
  const node: JsonLdNode = {
    "@type": type,
    "@id": webPageId(path),
    url: absoluteUrl(path),
    name,
    description,
    inLanguage: "en-AU",
    isPartOf: { "@id": WEBSITE_ID },
    publisher: { "@id": ORGANIZATION_ID },
  };
  if (updated) node.dateModified = updated;
  if (hasBreadcrumb) node.breadcrumb = { "@id": breadcrumbId(path) };
  return node;
}

export interface BreadcrumbItem {
  name: string;
  path: string;
}

export function buildBreadcrumbSchema(
  items: BreadcrumbItem[],
  path: string,
): JsonLdNode {
  return {
    "@type": "BreadcrumbList",
    "@id": breadcrumbId(path),
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(item.path),
    })),
  };
}

/**
 * The four nodes every indexable registry route gets, plus whatever that page
 * adds on top.
 *
 * The page facts come from `STATIC_PAGES`, so the `name`, `description` and
 * `dateModified` in the graph are the same strings as the `<title>`, the meta
 * description and the sitemap's `lastmod` — one source, not a second copy in
 * each `page.tsx` that would drift from the first.
 */
export function buildStaticPageGraph(
  path: PagePath,
  extra: JsonLdNode[] = [],
  webPageType?: string,
): JsonLdNode {
  const page: StaticPage = STATIC_PAGES[path];
  return buildGraph([
    buildOrganizationSchema(),
    buildWebSiteSchema(),
    buildWebPageSchema({
      path,
      name: page.title,
      description: page.description,
      updated: page.updated,
      type: webPageType,
    }),
    buildBreadcrumbSchema(breadcrumbItemsFor(path), path),
    ...extra,
  ]);
}

export interface FaqEntry {
  question: string;
  answer: string;
}

/**
 * FAQ markup for a page that visibly answers those questions.
 *
 * Google restricted FAQ rich results to well-known government and health sites
 * in August 2023, so this is not claimed as a rich-result outcome — it is
 * well-formed schema that answer engines still read. That is also why the copy
 * behind it has to be true rather than merely plausible: see
 * `data/pillar-faqs.ts`.
 */
export function buildFaqSchema(faqs: FaqEntry[]): JsonLdNode | null {
  if (faqs.length === 0) return null;
  return {
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: { "@type": "Answer", text: faq.answer },
    })),
  };
}

/* ------------------------------------------------------------------ *
 * Retailers and product lists
 * ------------------------------------------------------------------ */

/**
 * One canonical node per supermarket, so an offer's `seller` is a reference
 * rather than a fresh `Organization` minted per product per price.
 *
 * The `@id`s are SplitCart's identifiers for these entities — an `@id` is never
 * resolved across sites — and `url` is each retailer's real homepage, which is
 * the only claim being made about them here.
 */
const RETAILER_URLS: Record<string, string> = {
  Coles: "https://www.coles.com.au",
  Woolworths: "https://www.woolworths.com.au",
  Aldi: "https://www.aldi.com.au",
  IGA: "https://www.iga.com.au",
};

export function retailerId(company: string): string {
  return `${SITE_URL}/#retailer-${company.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}

export function buildRetailerSchemas(companies: string[]): JsonLdNode[] {
  return [...new Set(companies)].sort().map((company) => {
    const node: JsonLdNode = {
      "@type": "Organization",
      "@id": retailerId(company),
      name: company,
    };
    const url = RETAILER_URLS[company];
    if (url) node.url = url;
    return node;
  });
}

/** `"$3.45"` → `3.45`. Returns null for anything that is not a clean number. */
function parsePrice(display: string | undefined): number | null {
  if (!display) return null;
  const value = Number.parseFloat(display.replace(/[^0-9.]/g, ""));
  return Number.isFinite(value) ? value : null;
}

/**
 * An `ItemList` of the products a carousel shows.
 *
 * This is a product *snippet* aggregation, not a merchant listing: SplitCart
 * does not sell any of these, it reports what three supermarkets charge. Google
 * documents `AggregateOffer` (`lowPrice`/`highPrice`/`offerCount`/
 * `priceCurrency`) for exactly this case.
 *
 * What is deliberately absent, and must stay absent until it is true:
 * `availability` (no live stock state reaches this codebase — the scrape
 * carries prices, not stock), `shippingDetails` and `hasMerchantReturnPolicy`
 * (they would be Coles' and Woolworths' terms, which SplitCart neither sets nor
 * honours). Publishing the easy half of an offer and inventing the rest is the
 * seo-standard.md section 0 violation that carries a manual action rather than
 * a missed feature.
 *
 * No `Product.url` either: product pages are robots-disallowed, so linking one
 * from schema points a crawler at a URL it is told not to fetch.
 */
export function buildProductItemListSchema(
  products: Product[],
  name: string,
): JsonLdNode | null {
  const items = products
    .map((product, index) => {
      const offers = product.prices
        .map((priceInfo) => ({
          company: priceInfo.company,
          price: parsePrice(priceInfo.price_display),
        }))
        .filter(
          (offer): offer is { company: string; price: number } =>
            offer.price !== null,
        );

      if (offers.length === 0) return null;

      const prices = offers.map((offer) => offer.price);
      const item: JsonLdNode = {
        "@type": "Product",
        name: product.name,
        offers: {
          "@type": "AggregateOffer",
          priceCurrency: "AUD",
          lowPrice: Math.min(...prices).toFixed(2),
          highPrice: Math.max(...prices).toFixed(2),
          offerCount: offers.length,
          offers: offers.map((offer) => ({
            "@type": "Offer",
            price: offer.price.toFixed(2),
            priceCurrency: "AUD",
            seller: { "@id": retailerId(offer.company) },
          })),
        },
      };
      if (product.image_url) item.image = product.image_url;
      if (product.brand_name) {
        item.brand = { "@type": "Brand", name: product.brand_name };
      }

      const listItem: JsonLdNode = {
        "@type": "ListItem",
        position: index + 1,
        item,
      };
      return listItem;
    })
    .filter((entry): entry is JsonLdNode => entry !== null);

  if (items.length === 0) return null;

  return {
    "@type": "ItemList",
    name,
    numberOfItems: items.length,
    itemListElement: items,
  };
}

/** Every company named across a set of products, for `buildRetailerSchemas`. */
export function companiesIn(products: Product[]): string[] {
  return products.flatMap((product) =>
    product.prices.map((priceInfo) => priceInfo.company),
  );
}
