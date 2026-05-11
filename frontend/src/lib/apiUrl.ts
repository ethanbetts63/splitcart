const PUBLIC_API_URL = process.env.NEXT_PUBLIC_DJANGO_API_URL?.replace(/\/$/, "");
const PRODUCTION_API_URL = "https://api.splitcart.com.au";

const shouldUseProductionApiFallback = () => {
  if (typeof window === "undefined") return false;
  return window.location.hostname === "www.splitcart.com.au";
};

export const getApiUrl = (endpoint: string) => {
  if (/^https?:\/\//.test(endpoint)) return endpoint;

  const normalizedEndpoint = endpoint.startsWith("/api")
    ? endpoint
    : `/api${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const apiUrl = PUBLIC_API_URL || (shouldUseProductionApiFallback() ? PRODUCTION_API_URL : "");

  return apiUrl ? `${apiUrl}${normalizedEndpoint}` : normalizedEndpoint;
};
