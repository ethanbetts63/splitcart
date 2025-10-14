// --- Data Structures ---

export type CompanyPriceInfo = {
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
};

export type Store = {
  id: number;
  store_name: string;
  company_name: string;
  latitude: number;
  longitude: number;
};

export type MapCenter = {
  latitude: number;
  longitude: number;
  radius: number;
} | null;


// --- Context-Specific Types ---

export type CartItem = {
  product: Product;
  quantity: number;
};
