import React from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '@/hooks/useApiQuery';
import type { Product } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import PriceDisplay from '../components/PriceDisplay';
import AddToCartButton from '../components/AddToCartButton';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { ProductCarousel } from '../components/ProductCarousel';
import { useStoreList } from '../context/StoreListContext';
import Seo from '../components/Seo';

const ProductPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const { selectedStoreIds } = useStoreList();

  const storeIdsArray = React.useMemo(() => Array.from(selectedStoreIds), [selectedStoreIds]);

  // Extract the ID from the slug
  const productId = slug ? slug.split('-').pop() : undefined;

  // Construct the API URL with store_ids query parameter
  const storeIdsQuery = storeIdsArray.length > 0 ? `?store_ids=${storeIdsArray.join(',')}` : '';
  const apiUrl = `/api/products/${productId}/${storeIdsQuery}`;

  const { data: product, isLoading, error } = useApiQuery<Product>(
    ['product', productId, storeIdsArray.join(',')], // Add storeIds to query key for reactive updates
    apiUrl,
    {},
    { enabled: !!productId } // Only run query if productId is available
  );

  const pageTitle = product ? `${product.name} - Price Comparison` : 'SplitCart';
  const pageDescription = product
    ? `Compare prices for ${product.name}${product.brand_name ? ` from ${product.brand_name}` : ''} across major Australian supermarkets. Find the best deals with SplitCart.`
    : 'Compare prices across major Australian supermarkets and find the best deals with SplitCart.';

  const productSchema = product ? {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    image: product.image_url,
    description: pageDescription,
    sku: product.id,
    brand: product.brand_name ? {
      '@type': 'Brand',
      name: product.brand_name,
    } : undefined,
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: 'AUD',
      lowPrice: Math.min(...product.prices.map(p => parseFloat(p.price_display.replace('
};

export default ProductPage;
