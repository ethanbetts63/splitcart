'use client';

import { cva } from 'class-variance-authority';

import { Badge } from './common/badge';
import type { PriceDisplayProps } from '../types/PriceDisplayProps';
import { companyLogos } from '@/lib/companies';

/**
 * One boolean, `is_lowest`, decided three separate class strings here, each
 * written as its own ternary inside its own template literal. That is the
 * copied-class-bundle shape LINT-3 names: nothing holds the three answers
 * together, so a change to what "cheapest" looks like has to be made three
 * times and can be made twice. One variant set, three slots.
 */
const priceRowVariants = cva('p-2 rounded-md', {
  variants: {
    emphasis: {
      lowest: 'bg-surface-success border border-border-success',
      standard: 'bg-surface-muted',
    },
  },
  defaultVariants: { emphasis: 'standard' },
});

const priceCompanyVariants = cva('text-lead', {
  variants: {
    emphasis: {
      lowest: 'font-bold text-text-primary',
      standard: 'text-text-secondary',
    },
  },
  defaultVariants: { emphasis: 'standard' },
});

const priceAmountVariants = cva('text-lead font-semibold', {
  variants: {
    emphasis: {
      lowest: 'text-text-success',
      standard: 'text-text-primary',
    },
  },
  defaultVariants: { emphasis: 'standard' },
});

const CompanyLogo = ({
  companyName,
  priceDisplay,
}: {
  companyName: string;
  priceDisplay: string;
}) => {
  const logoSrc = companyLogos[companyName];

  if (!logoSrc) {
    return <div className="h-5 w-5 rounded-sm bg-surface-sunken-strong" />;
  }

  return (
    <img
      src={logoSrc}
      alt={companyName}
      className="h-5 w-5 rounded-sm object-contain"
      width="20"
      height="20"
      title={`${companyName}: ${priceDisplay}`}
    />
  );
};

const PriceDisplay = ({ prices, displayMode = 'compact' }: PriceDisplayProps) => {
  if (!prices || prices.length === 0) {
    return <p className="text-body text-text-subtle">No price available</p>;
  }

  // Full display mode — product page
  if (displayMode === 'full') {
    return (
      <div className="grid gap-2">
        {prices.map((priceInfo) => {
          const emphasis = priceInfo.is_lowest ? 'lowest' : 'standard';
          return (
            <div key={priceInfo.company} className={priceRowVariants({ emphasis })}>
              <div className="flex justify-center items-center gap-4">
                <div className="flex items-center gap-3">
                  <CompanyLogo
                    companyName={priceInfo.company}
                    priceDisplay={priceInfo.price_display}
                  />
                  <span className={priceCompanyVariants({ emphasis })}>{priceInfo.company}</span>
                </div>
                <div className="flex items-center gap-2">
                  {priceInfo.is_lowest && (
                    <Badge
                      variant="secondary"
                      className="bg-surface-success-strong text-text-success"
                    >
                      Lowest
                    </Badge>
                  )}
                  <span className={priceAmountVariants({ emphasis })}>
                    {priceInfo.price_display}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Compact mode — tile
  const lowestPriceStr = prices[0].price_display.split(' - ')[0];
  const highestPriceRange = prices[prices.length - 1].price_display.split(' - ');
  const highestPriceStr = highestPriceRange[highestPriceRange.length - 1];
  const isRange = lowestPriceStr !== highestPriceStr;

  return (
    <div className="flex items-center justify-between gap-2">
      <p className="font-bold text-text-primary leading-none">
        {isRange && <span className="text-caption font-normal text-text-subtle mr-0.5">from </span>}
        <span className="text-body">${lowestPriceStr}</span>
      </p>
      <div className="flex items-center gap-1">
        {prices.map((priceInfo) => (
          <CompanyLogo
            key={priceInfo.company}
            companyName={priceInfo.company}
            priceDisplay={priceInfo.price_display}
          />
        ))}
      </div>
    </div>
  );
};

export default PriceDisplay;
