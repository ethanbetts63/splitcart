import React from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '@/hooks/useApiQuery';
import type { Product } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import PriceDisplay from '../components/PriceDisplay';
import AddToCartButton from '../components/AddToCartButton';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import Seo from '../components/Seo';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { ProductCarousel } from '../components/ProductCarousel';
import { useStoreList } from '../context/StoreListContext';

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
      lowPrice: Math.min(...product.prices.map(p => parseFloat(p.price_display.replace('$', '')))).toFixed(2),
      highPrice: Math.max(...product.prices.map(p => parseFloat(p.price_display.replace('$', '')))).toFixed(2),
      offerCount: product.prices.length,
      offers: product.prices.map(priceInfo => ({
        '@type': 'Offer',
        price: parseFloat(priceInfo.price_display.replace('$', '')).toFixed(2),
        priceCurrency: 'AUD',
        seller: {
          '@type': 'Organization',
          name: priceInfo.company,
        },
        url: `https://www.splitcart.com.au/product/${product.slug}`
      })),
    },
  } : null;

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: Could not load product details.</div>;
  }

  if (!product) {
    return <div className="text-center p-4">Product not found.</div>;
  }
  const imageUrl = product.image_url || fallbackImage;

  return (
    <div className="container mx-auto p-4 md:p-4">
      <Seo
        title={pageTitle}
        description={pageDescription}
        canonicalPath={`/product/${slug}`}
        structuredData={productSchema}
      />
      <div className="max-w-5xl mx-auto">
        <Card className="overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
            {/* Image Column */}
            <div className="aspect-square w-full overflow-hidden">
               <img
                src={imageUrl}
                alt={product.name}
                className="h-full w-full object-cover"
              />
            </div>

            {/* Details Column */}
            <div className="flex flex-col p-2">
              <CardHeader className="p-0">
                <CardTitle className="text-2xl lg:text-3xl font-bold">{product.name}</CardTitle>
                {product.brand_name && (
                  <CardDescription className="text-xl lg:text-2xl text-muted-foreground pt-2">
                    {product.brand_name}
                  </CardDescription>
                )}
                 {product.size && (
                  <CardDescription className="text-lg text-muted-foreground pt-1">
                    {product.size}
                  </CardDescription>
                )}
              </CardHeader>

              <CardContent className="flex-grow p-0 mt-6 w-full">
                <h3 className="text-lg font-semibold mb-4 text-center">Price Comparison</h3>
                <PriceDisplay prices={product.prices} displayMode="full" />
              </CardContent>

              <div className="mt-auto pt-6 flex justify-center">
                <AddToCartButton product={product} />
              </div>
            </div>
          </div>
        </Card>

        <div className="mt-12">
          <ProductCarousel
            key={`substitutes-for-${product.id}`}
            title="Similar Products"
            sourceUrl={`/api/products/${product.id}/substitutes/`}
            storeIds={storeIdsArray}
            minProducts={1}
          />
        </div>
      </div>
    </div>
  );
};

export default ProductPage;