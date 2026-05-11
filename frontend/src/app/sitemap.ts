import type { MetadataRoute } from "next";

const baseUrl = "https://www.splitcart.com.au";

const categoryPaths = [
  "/categories/baby/",
  "/categories/bakery-and-deli/",
  "/categories/dairy-and-eggs/",
  "/categories/drinks/",
  "/categories/fruit-and-veg/",
  "/categories/health-beauty-and-supplements/",
  "/categories/home-cleaning-gardening-and-pets/",
  "/categories/international-herbs-and-spices/",
  "/categories/meat-and-seafood/",
  "/categories/pantry/",
  "/categories/snacks-and-sweets/",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return [
    {
      url: `${baseUrl}/`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/contact`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/bargains`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.8,
    },
    ...categoryPaths.map((path) => ({
      url: `${baseUrl}${path}`,
      lastModified: now,
      changeFrequency: "weekly" as const,
      priority: 0.9,
    })),
  ];
}
