'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import Link from 'next/link';
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import placeholderImage from '../assets/placeholder.webp';
import type { ProductTileProps } from '../types/ProductTileProps';
import { assetSrc } from '@/lib/assets';
import { cn } from '@/lib/utils';

const ProductTile: React.FC<ProductTileProps> = ({
  product,
  root = null,
  rootMargin = '200px 0px 200px 0px',
}) => {
  const [isButtonHovered, setIsButtonHovered] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const tileRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    // If a custom root is provided (like in a carousel), we need to ensure it's actually mounted.
    // However, the IntersectionObserver API handles 'null' as the viewport correctly.
    // The issue is if 'root' is passed as a ref.current that might be null initially.
    // But since we are passing 'root' as a prop, the parent component handles that.

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      {
        root: root,
        rootMargin: rootMargin,
        threshold: 0.01,
      },
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
  }, [isVisible, root, rootMargin]);

  const fallbackImageUrl = assetSrc(fallbackImage);
  const placeholderImageUrl = assetSrc(placeholderImage);
  const imageUrl = isVisible ? product.image_url || fallbackImageUrl : placeholderImageUrl;

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    if (e.currentTarget.src !== fallbackImageUrl) {
      e.currentTarget.src = fallbackImageUrl;
    }
  };

  const bargainInfo = useMemo(() => {
    if (!product.bargain_info) return null;

    const companyShortNames: { [key: string]: string } = {
      Woolworths: 'Woolies',
      Coles: 'Coles',
      Aldi: 'Aldi',
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
    } catch {
      // Not valid JSON, use original string
    }
  }

  if (!product.slug) {
    return (
      <div className="rounded-xl border border-border-default bg-surface-page shadow-sm overflow-hidden opacity-50 h-full" />
    );
  }

  return (
    <Link href={`/product/${product.slug}`} className="group block h-full" ref={tileRef}>
      <div
        className={cn(
          'flex flex-col h-full rounded-xl border border-border-default bg-surface-page shadow-sm overflow-hidden transition-all duration-200',
          !isButtonHovered &&
            'group-hover:shadow-md group-hover:border-action-primary group-hover:-translate-y-0.5',
        )}
      >
        {/* Image */}
        <div className="relative aspect-square w-full overflow-hidden bg-surface-muted">
          {bargainInfo && (
            <span className="absolute top-2 left-2 z-20 text-label font-bold px-2.5 py-1 rounded-full shadow-md bg-surface-inverse/80 backdrop-blur-sm text-text-on-dark">
              <span className="text-accent-on-dark">-{bargainInfo.percentage}%</span> at{' '}
              {bargainInfo.cheapestCompany}
            </span>
          )}
          <div className="absolute bottom-2 right-2 z-20 flex flex-col items-end gap-1">
            {perUnitPriceString && (
              <span className="text-label bg-surface-page/90 backdrop-blur-sm text-text-control font-medium px-1.5 py-0.5 rounded-md shadow-sm">
                {perUnitPriceString}
              </span>
            )}
            {displaySize && (
              <span className="text-label bg-surface-page/90 backdrop-blur-sm text-text-control font-medium px-1.5 py-0.5 rounded-md shadow-sm">
                {displaySize}
              </span>
            )}
          </div>
          <img
            src={imageUrl}
            onError={handleImageError}
            alt={product.name}
            className={cn(
              'h-full w-full object-cover transition-transform duration-300',
              !isButtonHovered && 'group-hover:scale-105',
            )}
            loading={isVisible ? 'eager' : 'lazy'}
          />
        </div>

        {/* Content */}
        <div className="flex flex-col flex-grow p-3 gap-2">
          {/* Name + Brand */}
          <div>
            <h3
              className={cn(
                'font-bold text-text-primary text-body leading-snug line-clamp-2',
                !isButtonHovered && 'group-hover:underline',
              )}
            >
              {product.name}
            </h3>
            {product.brand_name && (
              <p className="text-caption text-text-subtle mt-0.5 truncate">{product.brand_name}</p>
            )}
          </div>

          {/* Price */}
          <div className="mt-auto pt-2 border-t border-border-subtle">
            <PriceDisplay prices={product.prices} />
          </div>

          {/* Add to Cart */}
          <div
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
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
