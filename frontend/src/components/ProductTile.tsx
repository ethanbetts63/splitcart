import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
  const [isButtonHovered, setIsButtonHovered] = useState(false);

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
    // Use the new pre-calculated bargain_info from the API
    if (!product.bargain_info) {
      return null;
    }

    const companyShortNames: { [key: string]: string } = {
      "Woolworths": "Woolies",
      "Coles": "Coles",
      "IGA": "IGA",
      "Aldi": "Aldi",
    };

    const companyColors: { [key: string]: string } = {
      "Aldi": "bg-blue-300 text-black font-bold",
      "Woolies": "bg-green-500 text-black font-bold",
      "Coles": "bg-red-700 text-white font-bold",
      "IGA": "bg-black text-white border border-red-600 font-bold",
    };

    const companyName = product.bargain_info.cheapest_company_name;
    const shortName = companyShortNames[companyName] || companyName;

    const bargainBadgeClasses = companyColors[shortName] || "bg-gray-700 text-white font-bold";

    return {
      percentage: product.bargain_info.discount_percentage,
      cheapestCompany: shortName,
      bargainBadgeClasses: bargainBadgeClasses,
    };
  }, [product.bargain_info]);

  const cheapestPriceInfo = product.prices && product.prices.length > 0 ? product.prices[0] : null;
  const perUnitPriceString = cheapestPriceInfo?.per_unit_price_string;

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
  
  if (!product.slug) {
    // Render a non-clickable version or a placeholder if there's no slug
    return (
      <Card className="flex flex-col h-full overflow-hidden gap-1 pt-0 pb-2 opacity-50">
        {/* Simplified content for when it's not linkable */}
      </Card>
    );
  }

  return (
    <Link to={`/product/${product.slug}`} className="group block h-full">
      <Card className={`flex flex-col h-full overflow-hidden gap-1 pt-0 pb-2 transition-shadow duration-200 ${!isButtonHovered && 'group-hover:shadow-lg'}`}>
        <div className="aspect-square w-full overflow-hidden relative">
          <div className="absolute top-2 right-2 z-20 flex flex-col items-end gap-1">
            {bargainInfo && (
              <Badge className={`${bargainInfo.bargainBadgeClasses} text-sm py-px px-1.5`}>
                -{bargainInfo.percentage}% at {bargainInfo.cheapestCompany}
              </Badge>
            )}
            {perUnitPriceString && (
              <Badge>{perUnitPriceString}</Badge>
            )}
            {displaySize && (
              <Badge>{displaySize}</Badge>
            )}
          </div>
          <img
            src={imageUrl}
            srcSet={srcSet}
            sizes="273px"
            onError={handleImageError}
            alt={product.name}
            className={`h-full w-full object-cover transition-transform duration-200 ${!isButtonHovered && 'group-hover:scale-105'}`}
          />
        </div>
        <CardHeader className="p-0 text-center">
          <CardTitle className={`h-12 leading-5 text-base font-semibold overflow-hidden text-ellipsis line-clamp-2 ${!isButtonHovered && 'group-hover:underline'}`}>{product.name}</CardTitle>
          {product.brand_name && <CardDescription className="text-sm text-muted-foreground">{product.brand_name}</CardDescription>}
        </CardHeader>
        <CardContent className="flex-grow px-3">
          <PriceDisplay prices={product.prices} />
        </CardContent>
        <CardFooter className="flex justify-center pb-0">
          <div 
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onMouseEnter={() => setIsButtonHovered(true)}
            onMouseLeave={() => setIsButtonHovered(false)}
          >
            <AddToCartButton product={product} />
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
};

export default ProductTile;