import type { Product } from './Product';

export type PaginatedProductResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Product[];
};
