import type { NextConfig } from "next";

const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  images: {
    disableStaticImages: true,
  },
  async redirects() {
    return [
      {
        source: "/pillar-pages/eggs-and-dairy/",
        destination: "/categories/dairy-and-eggs/",
        permanent: true,
      },
      {
        source: "/pillar-pages/eggs/",
        destination: "/categories/dairy-and-eggs/",
        permanent: true,
      },
      {
        source: "/pillar-pages/pet-and-baby/",
        destination: "/categories/baby/",
        permanent: true,
      },
      {
        source: "/pillar-pages/fruit-veg-and-spices/",
        destination: "/categories/fruit-and-veg/",
        permanent: true,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
