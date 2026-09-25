import type { Metadata } from "next";

export const siteUrl = "https://www.splitcart.com.au";
export const siteName = "SplitCart";

/**
 * The one fallback link-preview image, and its real dimensions.
 *
 * This constant pointed at `/static/square-image.jpg` until 2026-09-25 — a path
 * with no file behind it and no `/static/` directory in `public/` at all. It is
 * applied by `createMetadata()` to every page, so every social share of every
 * SplitCart URL linked a 404 rather than showing a card. `check:og-images`
 * exists so that cannot come back silently.
 *
 * Only the default asset carries width and height: a page-supplied image would
 * be a photograph whose size the metadata builder does not know, and stating it
 * wrongly is worse than omitting it.
 */
export const defaultOgImage = "/og-default.png";
export const defaultOgWidth = 1200;
export const defaultOgHeight = 630;

type SeoMetadataOptions = {
  title: string;
  description?: string;
  canonicalPath?: string;
  noindex?: boolean;
};

export function createMetadata({
  title,
  description,
  canonicalPath,
  noindex = false,
}: SeoMetadataOptions): Metadata {
  const canonicalUrl = canonicalPath ? `${siteUrl}${canonicalPath}` : undefined;

  return {
    title,
    description,
    alternates: canonicalUrl
      ? {
          canonical: canonicalUrl,
        }
      : undefined,
    robots: noindex
      ? {
          index: false,
          follow: false,
        }
      : undefined,
    openGraph: {
      title,
      description,
      url: canonicalUrl,
      siteName,
      type: "website",
      images: [
        { url: defaultOgImage, width: defaultOgWidth, height: defaultOgHeight },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [defaultOgImage],
    },
  };
}

export const noindexMetadata = createMetadata({
  title: "SplitCart",
  noindex: true,
});
