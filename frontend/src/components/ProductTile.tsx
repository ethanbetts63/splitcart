import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';

import { Badge } from "./ui/badge";
import type { Product } from '../types'; // Import shared type

interface ProductTileProps {
  product: Product;
}

const ProductTile: React.FC<ProductTileProps> = ({ product }) => {
  const [imageUrl, setImageUrl] = useState(product.image_url || fallbackImage);

  // Effect to reset the image URL when the product prop changes
  useEffect(() => {
    setImageUrl(product.image_url || fallbackImage);
  }, [product.image_url]);

  const handleImageError = () => {
    // Prevent a loop if the fallback image itself is broken
    if (imageUrl !== fallbackImage) {
      setImageUrl(fallbackImage);
    }
  };

  const generateSrcSet = (url: string) => {
    if (!url.includes('cdn.metcash.media')) {
      return undefined;
    }
    const sizes = [200, 250, 300, 350, 400, 450, 500];
    return sizes
      .map(size => `${url.replace('w_1500,h_1500', `w_${size},h_${size},f_auto`)} ${size}w`)
      .join(', ');
  };

  const srcSet = generateSrcSet(imageUrl);

  const bargainInfo = React.useMemo(() => {
    if (!product.prices || product.prices.length <= 1) {
      return null;
    }

    const companyShortNames: { [key: string]: string } = {
      "Woolworths": "Woolies",
      "Coles": "Coles",
      "IGA": "IGA",
      "Aldi": "Aldi",
    };

    const companyColors: { [key: string]: string } = {
      "Aldi": "bg-blue-300 text-gray-800", // Light blue, dark text for contrast
      "Woolies": "bg-green-500 text-white", // Green, white text
      "Coles": "bg-red-500 text-white", // Red, white text
      "IGA": "bg-white text-red-600 border border-red-600", // White, red text, red border
    };

    // Parse prices to numbers and filter out invalid ones
    const numericPrices = product.prices.map(p => ({
      company: p.company,
      price: parseFloat(p.price_display.replace('$', '')), // Assuming price_display is like "$X.YY"
    })).filter(p => !isNaN(p.price));

    if (numericPrices.length <= 1) {
      return null; // Not enough valid prices to compare
    }

    const minPrice = Math.min(...numericPrices.map(p => p.price));
    const maxPrice = Math.max(...numericPrices.map(p => p.price));

    if (minPrice === maxPrice) {
      return null; // No difference
    }

    const percentage = Math.round(((maxPrice - minPrice) / maxPrice) * 100);
    const cheapestCompanies = numericPrices
      .filter(p => p.price === minPrice)
      .map(p => companyShortNames[p.company] || p.company); // Use mapped name or fallback

    const bargainBadgeClasses = cheapestCompanies.length === 1
      ? companyColors[cheapestCompanies[0]] || "bg-gray-700 text-white" // Default if company not found
      : "bg-gray-700 text-white"; // Default for multiple companies

    return { percentage, cheapestCompanies, bargainBadgeClasses };
  }, [product.prices]);

  const cheapestPriceInfo = product.prices && product.prices.length > 0 ? product.prices[0] : null;
  const perUnitPriceString = cheapestPriceInfo?.per_unit_price_string;

  // Defensively handle the size property in case it's a stringified array
  let displaySize = product.size;
  if (product.size && typeof product.size === 'string' && product.size.startsWith('[')) {
    try {
      const sizes = JSON.parse(product.size);
      if (Array.isArray(sizes) && sizes.length > 0) {
        displaySize = sizes[0];
      }
    } catch (e) {
      // Not valid JSON, so we'll just use the original string.
    }
  }

  let currentTopPosition = 2; // Initial top position for the first badge

  const getNextTopPosition = (hasBadge: boolean) => {
    if (hasBadge) {
      const position = currentTopPosition;
      currentTopPosition += 6; // Increment by 6 (tailwind 'top-8' is 6 units more than 'top-2')
      return `top-${position}`;
    }
    return ''; // No badge, no position
  };


  return (
    <Card className="flex flex-col h-full overflow-hidden gap-1 pt-0 pb-2">
      <div className="aspect-square w-full overflow-hidden relative">
        {perUnitPriceString && (
          <Badge className={`absolute ${getNextTopPosition(true)} right-2 z-20`}>{perUnitPriceString}</Badge>
        )}
        {bargainInfo && (
          <Badge className={`absolute ${getNextTopPosition(true)} right-2 z-20 ${bargainInfo.bargainBadgeClasses}`}>
            -{bargainInfo.percentage}% at {bargainInfo.cheapestCompanies.join(' or ')}
          </Badge>
        )}
        {displaySize && (
          <Badge className={`absolute ${getNextTopPosition(true)} right-2 z-20`}>{displaySize}</Badge>
        )}
        <img
          src={imageUrl}
          srcSet={srcSet}
          sizes="273px"
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover transition-transform hover:scale-105"
        />
      </div>
      <CardHeader className="p-0 text-center">
        <CardTitle className="h-12 leading-5 text-base font-semibold overflow-hidden text-ellipsis line-clamp-2">{product.name}</CardTitle>
        {product.brand_name && <CardDescription className="text-sm text-muted-foreground">{product.brand_name}</CardDescription>}
      </CardHeader>
      <CardContent className="flex-grow px-3">
        <PriceDisplay prices={product.prices} />
      </CardContent>
      <CardFooter className="flex justify-center pb-0">
        <AddToCartButton product={product} />
      </CardFooter>
    </Card>
  );
};

export default ProductTile;