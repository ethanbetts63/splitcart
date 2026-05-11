import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      disallow: [
        "/admin/",
        "/api/",
        "/substitutions/",
        "/final-cart/",
        "/search",
        "/login",
        "/signup",
        "/product/",
      ],
    },
    sitemap: "https://www.splitcart.com.au/sitemap.xml",
  };
}
