export type CompanyPriceInfo = {
  company: string;
  price_display: string;
  is_lowest: boolean;
  image_url?: string;
  per_unit_price_string?: string;
  /** ISO date the price was scraped. */
  scraped_date?: string;
};
