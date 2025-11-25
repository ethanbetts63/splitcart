import React, { useEffect } from 'react';
import type { Product } from '../types';

interface JsonLdProductProps {
  product: Product;
}

const JsonLdProduct: React.FC<JsonLdProductProps> = ({ product }) => {

  useEffect(() => {
    if (!product) {
      return;
    }

    const offers = product.prices.map(priceInfo => ({
      '@type': 'Offer',
      price: parseFloat(priceInfo.price_display.replace('$', '')).toFixed(2),
      priceCurrency: 'AUD',
      seller: {
        '@type': 'Organization',
        name: priceInfo.company,
      },
      url: `https://www.splitcart.com/product/${product.slug}` // Assuming this is the canonical URL
    }));

    const lowPrice = Math.min(...offers.map(o => parseFloat(o.price)));
    const highPrice = Math.max(...offers.map(o => parseFloat(o.price)));

    const structuredData = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: product.name,
      image: product.image_url,
      description: `Compare prices for ${product.name}${product.brand_name ? ` from ${product.brand_name}` : ''} across major Australian supermarkets.`,
      sku: product.id, // Using internal ID as a SKU
      brand: product.brand_name ? {
        '@type': 'Brand',
        name: product.brand_name,
      } : undefined,
      offers: {
        '@type': 'AggregateOffer',
        priceCurrency: 'AUD',
        lowPrice: lowPrice.toFixed(2),
        highPrice: highPrice.toFixed(2),
        offerCount: offers.length,
        offers: offers,
      },
    };

    const scriptId = 'json-ld-product';
    // Remove existing script to prevent duplicates on re-render
    const existingScript = document.getElementById(scriptId);
    if (existingScript) {
      existingScript.remove();
    }

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = scriptId;
    script.innerHTML = JSON.stringify(structuredData);
    
    document.head.appendChild(script);

    // Cleanup function to remove the script when the component unmounts
    return () => {
      const scriptElement = document.getElementById(scriptId);
      if (scriptElement) {
        scriptElement.remove();
      }
    };
  }, [product]); // Re-run effect if product changes

  return null; // This component doesn't render anything visible
};

export default JsonLdProduct;
