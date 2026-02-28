import React, { useEffect } from 'react';
import type { JsonLdItemListProps } from '../types/JsonLdItemListProps';

const JsonLdItemList: React.FC<JsonLdItemListProps> = ({ products, title }) => {

  useEffect(() => {
    if (!products || products.length === 0) {
      return;
    }

    const itemListElement = products.map((product, index) => {
      const offers = product.prices.map(priceInfo => ({
        '@type': 'Offer',
        price: parseFloat(priceInfo.price_display.replace('$', '')).toFixed(2),
        priceCurrency: 'AUD',
        seller: {
          '@type': 'Organization',
          name: priceInfo.company,
        },
      }));

      const lowPrice = Math.min(...offers.map(o => parseFloat(o.price)));
      const highPrice = Math.max(...offers.map(o => parseFloat(o.price)));

      return {
        '@type': 'ListItem',
        position: index + 1,
        item: {
          '@type': 'Product',
          name: product.name,
          image: product.image_url,
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
          // If we create product pages, we'll add the URL here
          // url: `https://www.splitcart.com/product/${product.slug}` 
        },
      };
    });

    const structuredData = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: title,
      itemListElement: itemListElement,
    };

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.innerHTML = JSON.stringify(structuredData);
    script.id = `json-ld-item-list-${title.replace(/\s+/g, '-')}`; // Unique ID for cleanup

    document.head.appendChild(script);

    // Cleanup function to remove the script when the component unmounts
    return () => {
      const existingScript = document.getElementById(script.id);
      if (existingScript) {
        document.head.removeChild(existingScript);
      }
    };
  }, [products, title]); // Re-run effect if products or title change

  return null; // This component doesn't render anything visible
};

export default JsonLdItemList;
