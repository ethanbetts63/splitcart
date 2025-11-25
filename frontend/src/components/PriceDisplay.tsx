import React from 'react';
import type { CompanyPriceInfo } from '../types'; // Import shared type
import { useCompanyLogo } from '../hooks/useCompanyLogo';
import { Skeleton } from './ui/skeleton';
import { Badge } from './ui/badge';

interface PriceDisplayProps {
  prices: CompanyPriceInfo[];
  displayMode?: 'compact' | 'full';
}

// Internal component to handle the logo loading state
const CompanyLogo = ({ companyName, priceDisplay }: { companyName: string; priceDisplay: string }) => {
  const { objectUrl, isLoading, error } = useCompanyLogo(companyName);

  if (isLoading) {
    return <Skeleton className="h-6 w-6 rounded-sm" />;
  }

  if (error || !objectUrl) {
    return <div className="h-6 w-6 rounded-sm bg-gray-200" />; // Placeholder for error/missing
  }

  return (
    <img 
      src={objectUrl} 
      alt={companyName} 
      className="h-6 w-6 rounded-sm object-contain"
      width="24"
      height="24"
      title={`${companyName}: ${priceDisplay}`}
    />
  );
};

const PriceDisplay: React.FC<PriceDisplayProps> = ({ prices, displayMode = 'compact' }) => {
  if (!prices || prices.length === 0) {
    return <p className="text-sm text-muted-foreground">No price available</p>;
  }

  // 'Full' display mode for Product Page
  if (displayMode === 'full') {
    return (
      <div className="grid gap-2">
        {prices.map((priceInfo) => (
          <div key={priceInfo.company} className={`p-2 rounded-md ${priceInfo.is_lowest ? 'bg-green-50 border border-green-200' : 'bg-gray-50'}`}>
            <div className="flex justify-center items-center gap-4">
              <div className="flex items-center gap-3">
                <CompanyLogo 
                  companyName={priceInfo.company} 
                  priceDisplay={priceInfo.price_display} 
                />
                <span className={`text-lg ${priceInfo.is_lowest ? 'font-bold text-gray-800' : 'text-gray-600'}`}>
                  {priceInfo.company}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {priceInfo.is_lowest && <Badge variant="secondary" className="bg-green-100 text-green-800">Lowest</Badge>}
                <span className={`text-xl font-semibold ${priceInfo.is_lowest ? 'text-green-700' : 'text-gray-800'}`}>
                  {priceInfo.price_display}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // 'Compact' display mode (default)
  const lowestPriceStr = prices[0].price_display.split(' - ')[0];
  const highestPriceRange = prices[prices.length - 1].price_display.split(' - ');
  const highestPriceStr = highestPriceRange[highestPriceRange.length - 1];

  const priceRange = lowestPriceStr === highestPriceStr 
    ? `${lowestPriceStr}` 
    : `${lowestPriceStr} - ${highestPriceStr}`;

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

