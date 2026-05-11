import type { Metadata } from "next";

export const siteUrl = "https://www.splitcart.com.au";
export const siteName = "SplitCart";
export const defaultOgImage = "/static/square-image.jpg";

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
      images: [defaultOgImage],
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
