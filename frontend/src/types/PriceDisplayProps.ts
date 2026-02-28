import type { CompanyPriceInfo } from './CompanyPriceInfo';

export interface PriceDisplayProps {
  prices: CompanyPriceInfo[];
  displayMode?: 'compact' | 'full';
}
