
// --- Data Structures ---

type CompanyPriceInfo = {
  company: string;
  price_display: string;
  is_lowest: boolean;
  image_url?: string;
};

type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: CompanyPriceInfo[];
};

export { type CompanyPriceInfo, type Product };
