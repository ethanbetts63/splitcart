import type { MetadataRoute } from "next";

const baseUrl = "https://www.splitcart.com.au";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${baseUrl}/`,
      lastModified: "2026-06-29",
      changeFrequency: "daily",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/contact`,
      lastModified: "2026-06-29",
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/bargains`,
      lastModified: "2026-06-29",
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/categories/baby/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/bakery-and-deli/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/dairy-and-eggs/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/drinks/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/fruit-and-veg/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/health-beauty-and-supplements/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/home-cleaning-gardening-and-pets/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/international-herbs-and-spices/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/meat-and-seafood/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/pantry/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/categories/snacks-and-sweets/`,
      lastModified: "2026-06-29",
      changeFrequency: "weekly",
      priority: 0.9,
    },
  ];
}
