import React from 'react';
import type { CompanyPriceInfo } from '../types'; // Import shared type
import { useCompanyLogo } from '../hooks/useCompanyLogo';
import { Skeleton } from './ui/skeleton';

interface PriceDisplayProps {
  prices: CompanyPriceInfo[];
}

// Internal component to handle the logo loading state
const CompanyLogo = ({ companyName, priceDisplay }: { companyName: string; priceDisplay: string }) => {
  const { objectUrl, isLoading, error } = useCompanyLogo(companyName);

  if (isLoading) {
    return <Skeleton className="h-5 w-5 rounded-sm" />;
  }

  if (error || !objectUrl) {
    return null; // Or a placeholder for error
  }

  return (
    <img 
      src={objectUrl} 
      alt={companyName} 
      className="h-5 w-auto rounded-sm"
      title={`${companyName}: $${priceDisplay}`}
    />
  );
};

const PriceDisplay: React.FC<PriceDisplayProps> = ({ prices }) => {
  if (!prices || prices.length === 0) {
    return <p className="text-sm text-muted-foreground">No price available</p>;
  }

  const lowestPriceStr = prices[0].price_display.split(' - ')[0];
  const highestPriceRange = prices[prices.length - 1].price_display.split(' - ');
  const highestPriceStr = highestPriceRange[highestPriceRange.length - 1];

  const priceRange = lowestPriceStr === highestPriceStr 
    ? `$${lowestPriceStr}` 
    : `$${lowestPriceStr} - $${highestPriceStr}`;

  return (
    <div className="grid gap-2">
      <p className="text-lg font-semibold text-center">{priceRange}</p>
      <div className="flex items-center justify-center gap-2">
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
