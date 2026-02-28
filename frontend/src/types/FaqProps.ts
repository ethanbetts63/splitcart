import type { FaqItem } from './FaqItem';

export interface FaqProps {
  title: string;
  imageSrc: string;
  imageAlt: string;
  srcSet?: string;
  sizes?: string;
  faqs: FaqItem[];
}
