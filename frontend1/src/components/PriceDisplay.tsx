import React from 'react';
import { CompanyPriceInfo } from '@/types'; // Import shared type

// --- Asset Imports ---
import aldiLogo from '@/assets/ALDI_logo.svg';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

interface PriceDisplayProps {
  prices: CompanyPriceInfo[];
}

// --- Logo Mapping ---
const companyLogos: { [key: string]: string } = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

const PriceDisplay: React.FC<PriceDisplayProps> = ({ prices }) => {
  // The API already provides a sorted list, so we don't need to sort again.
  if (!prices || prices.length === 0) {
    return <p className="text-sm text-muted-foreground">No price available</p>;
  }

  // The API sends price_display as a string, e.g., "2.50" or "2.50 - 2.70"
  const lowestPriceStr = prices[0].price_display.split(' - ')[0];
  const highestPriceRange = prices[prices.length - 1].price_display.split(' - ');
  const highestPriceStr = highestPriceRange[highestPriceRange.length - 1];

  const priceRange = lowestPriceStr === highestPriceStr 
    ? `$${lowestPriceStr}` 
    : `$${lowestPriceStr} - $${highestPriceStr}`;

  return (
    <div className="grid gap-2">
      <p className="text-lg font-semibold">{priceRange}</p>
      <div className="flex items-center justify-start gap-2">
        {prices.map((priceInfo) => {
          const logo = companyLogos[priceInfo.company];
          return logo ? (
            <img 
              key={priceInfo.company} 
              src={logo} 
              alt={priceInfo.company} 
              className="h-5 w-auto rounded-sm"
              title={`${priceInfo.company}: $${priceInfo.price_display}`}
            />
          ) : null;
        })}
      </div>
    </div>
  );
};

export default PriceDisplay;
