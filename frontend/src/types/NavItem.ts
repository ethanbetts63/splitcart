import type { ElementType } from 'react';

export type NavItem = {
  name: string;
  icon: ElementType;
  isCloseButton?: boolean;
};
