import type { PrimaryCategory } from './PrimaryCategory';
import type { FaqItem } from './FaqItem';

export interface PillarPage {
  name: string;
  slug: string;
  hero_title: string;
  introduction_paragraph: string;
  image_path: string;
  primary_categories: PrimaryCategory[];
  faqs: FaqItem[];
}
