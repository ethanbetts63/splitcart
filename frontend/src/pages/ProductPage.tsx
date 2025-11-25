import React from 'react';
import { useParams } from 'react-router-dom';
import { useApiQuery } from '@/hooks/useApiQuery';
import type { Product } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import PriceDisplay from '../components/PriceDisplay';
import AddToCartButton from '../components/AddToCartButton';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import { useDocumentHead } from '../hooks/useDocumentHead';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import JsonLdProduct from '../components/JsonLdProduct';

const ProductPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();

  // Extract the ID from the slug
  const productId = slug ? slug.split('-').pop() : undefined;

  const { data: product, isLoading, error } = useApiQuery<Product>(
    ['product', productId],
    `/api/products/${productId}/`,
    {},
    { enabled: !!productId } // Only run query if productId is available
  );

  // Set document head metadata when product data is available
  const pageTitle = product ? `${product.name} - Price Comparison` : 'SplitCart';
  const pageDescription = product
    ? `Compare prices for ${product.name}${product.brand_name ? ` from ${product.brand_name}` : ''} across major Australian supermarkets. Find the best deals with SplitCart.`
    : 'Compare prices across major Australian supermarkets and find the best deals with SplitCart.';
  
  useDocumentHead(pageTitle, pageDescription);

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
      {product && <JsonLdProduct product={product} />}
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

        {/* Substitutes Carousel will go here */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-4">Substitutes</h2>
          {/* Placeholder for the ProductCarousel for substitutes */}
          <div className="p-8 text-center bg-gray-100 rounded-lg">
            <p>Substitute carousel coming soon.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductPage;
