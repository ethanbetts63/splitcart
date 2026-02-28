import type { ReactNode } from 'react';

export interface HeroProps {
  title: ReactNode;
  subtitle: ReactNode;
  imageAlt: string;
  ctaElement?: ReactNode;
}
