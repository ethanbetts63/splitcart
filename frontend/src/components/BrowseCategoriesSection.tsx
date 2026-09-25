import Link from 'next/link';
import { cva } from 'class-variance-authority';

import { assetSrc } from '@/lib/assets';
import { CATEGORIES } from '@/data/categories';

/**
 * The featured/standard split was a ternary inside a template literal, which
 * is a class bundle nothing can type-check and nothing else can reuse.
 */
const categoryCardVariants = cva(
  'group flex flex-col items-center text-center rounded-xl p-5 shadow-sm border transition-all duration-200 hover:shadow-md hover:-translate-y-0.5',
  {
    variants: {
      emphasis: {
        featured: 'bg-action-primary border-action-primary-hover hover:bg-action-primary-hover',
        standard: 'bg-surface-page border-border-default hover:border-action-primary',
      },
    },
    defaultVariants: { emphasis: 'standard' },
  },
);

export const BrowseCategoriesSection = () => {
  return (
    <div className="site-shell py-10">
      <h2 className="text-title font-bold tracking-tight text-text-primary mb-6 text-center">
        Browse Bargains by Category
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {CATEGORIES.map((cat) => (
          <Link
            key={cat.href}
            href={cat.href}
            className={categoryCardVariants({ emphasis: cat.featured ? 'featured' : 'standard' })}
          >
            <img src={assetSrc(cat.icon)} alt="" aria-hidden="true" className="w-14 h-14 mb-3" />
            <h3 className="font-bold text-text-primary text-body leading-tight">{cat.title}</h3>
            <p className="text-body-sm text-text-secondary mt-1 leading-snug hidden sm:block">
              {cat.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
};
