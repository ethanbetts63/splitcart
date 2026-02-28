import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Link } from 'react-router-dom';
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import placeholderImage from '../assets/placeholder.webp';
import type { ProductTileProps } from '../types/ProductTileProps';

const ProductTile: React.FC<ProductTileProps> = ({ product }) => {
  const [isButtonHovered, setIsButtonHovered] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const tileRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      {
        rootMargin: '0px 0px 100px 0px',
        threshold: 0.01,
      }
    );

    const currentRef = tileRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [isVisible]);

  const imageUrl = isVisible ? (product.image_url || fallbackImage) : placeholderImage;

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    if (e.currentTarget.src !== fallbackImage) {
      e.currentTarget.src = fallbackImage;
    }
  };

  const generateSrcSet = (url: string) => {
    if (!isVisible || !url.includes('cdn.metcash.media') || url === placeholderImage || url === fallbackImage) {
      return undefined;
    }
    const sizes = [200, 250, 300, 350, 400, 450, 500];
    return sizes
      .map(size => `${url.replace('w_1500,h_1500', `w_${size},h_${size},f_auto`)} ${size}w`)
      .join(', ');
  };

  const srcSet = generateSrcSet(product.image_url || '');

  const bargainInfo = useMemo(() => {
    if (!product.bargain_info) return null;

    const companyShortNames: { [key: string]: string } = {
      'Woolworths': 'Woolies',
      'Coles': 'Coles',
      'IGA': 'IGA',
      'Aldi': 'Aldi',
    };

    const companyName = product.bargain_info.cheapest_company_name;
    const shortName = companyShortNames[companyName] || companyName;

    return {
      percentage: product.bargain_info.discount_percentage,
      cheapestCompany: shortName,
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
      // Not valid JSON, use original string
    }
  }

  if (!product.slug) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden opacity-50 h-full" />
    );
  }

  return (
    <Link to={`/product/${product.slug}`} className="group block h-full" ref={tileRef}>
      <div
        className={`flex flex-col h-full rounded-xl border bg-white shadow-sm overflow-hidden transition-all duration-200 ${
          !isButtonHovered
            ? 'border-gray-200 group-hover:shadow-md group-hover:border-yellow-300 group-hover:-translate-y-0.5'
            : 'border-gray-200'
        }`}
      >
        {/* Image */}
        <div className="relative aspect-square w-full overflow-hidden bg-gray-50">
          {bargainInfo && (
            <span className="absolute top-2 left-2 z-20 text-xs font-bold px-2.5 py-1 rounded-full shadow-md bg-gray-900/80 backdrop-blur-sm text-white">
              <span className="text-yellow-300">-{bargainInfo.percentage}%</span>
              {' '}at {bargainInfo.cheapestCompany}
            </span>
          )}
          <div className="absolute bottom-2 right-2 z-20 flex flex-col items-end gap-1">
            {perUnitPriceString && (
              <span className="text-xs bg-white/90 backdrop-blur-sm text-gray-700 font-medium px-1.5 py-0.5 rounded-md shadow-sm">
                {perUnitPriceString}
              </span>
            )}
            {displaySize && (
              <span className="text-xs bg-white/90 backdrop-blur-sm text-gray-700 font-medium px-1.5 py-0.5 rounded-md shadow-sm">
                {displaySize}
              </span>
            )}
          </div>
          <img
            src={imageUrl}
            srcSet={srcSet}
            sizes="273px"
            onError={handleImageError}
            alt={product.name}
            className={`h-full w-full object-cover transition-transform duration-300 ${!isButtonHovered && 'group-hover:scale-105'}`}
            loading="lazy"
          />
        </div>

        {/* Content */}
        <div className="flex flex-col flex-grow p-3 gap-2">
          {/* Name + Brand */}
          <div>
            <h3
              className={`font-bold text-gray-900 text-sm leading-snug line-clamp-2 ${!isButtonHovered && 'group-hover:underline'}`}
            >
              {product.name}
            </h3>
            {product.brand_name && (
              <p className="text-xs text-gray-400 mt-0.5 truncate">{product.brand_name}</p>
            )}
          </div>

          {/* Price */}
          <div className="mt-auto pt-2 border-t border-gray-100">
            <PriceDisplay prices={product.prices} />
          </div>

          {/* Add to Cart */}
          <div
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onMouseEnter={() => setIsButtonHovered(true)}
            onMouseLeave={() => setIsButtonHovered(false)}
            className="[&>button]:w-full [&>*]:w-full"
          >
            <AddToCartButton product={product} />
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProductTile;
