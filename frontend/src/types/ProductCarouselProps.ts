import type { Product } from './Product';

export interface ProductCarouselProps {
  sourceUrl?: string;
  products?: Product[];
  storeIds?: number[];
  title: string;
  searchQuery?: string;
  isDefaultStores?: boolean;
  isUserDefinedList?: boolean;
  primaryCategorySlug?: string;
  primaryCategorySlugs?: string[];
  pillarPageLinkSlug?: string;
  companyName?: string;
  isBargainCarousel?: boolean;
  onValidation?: (slug: string, isValid: boolean, slot: number) => void;
  slot?: number;
  dataKey?: string;
  minProducts?: number;
  ordering?: string;
  isLoading?: boolean;
}
