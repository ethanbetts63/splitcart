
// --- Data Structures ---

type CompanyPriceInfo = {
  company: string;
  price_display: string;
  is_lowest: boolean;
  image_url?: string;
};

export type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: CompanyPriceInfo[];
  level?: string;
  level_description?: string;
};

export { type CompanyPriceInfo, type Product };
