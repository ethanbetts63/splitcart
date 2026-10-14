import type { Product } from '../types';
import PriceDisplay from '../components/PriceDisplay';
import AddToCartButton from '../components/AddToCartButton';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import { Card, CardContent, CardHeader, CardDescription } from '../components/common/card';
import { ProductCarousel } from '../components/ProductCarousel';
import { assetSrc } from '@/lib/assets';
import { notFound } from 'next/navigation';
import { priceSummary, pricesChecked } from '@/lib/productPage';

type ProductPageProps = {
  product: Product | null;
};

const ProductPage = ({ product }: ProductPageProps) => {
  if (!product) notFound();

  const imageUrl = product.image_url || assetSrc(fallbackImage);
  const summary = priceSummary(product);
  const checked = pricesChecked(product);

  return (
    <div className="site-shell py-4">
      <div className="max-w-shell mx-auto">
        <Card className="overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
            {/* Image Column */}
            <div className="aspect-square w-full overflow-hidden">
              <img src={imageUrl} alt={product.name} className="h-full w-full object-cover" />
            </div>

            {/* Details Column */}
            <div className="flex flex-col p-2">
              <CardHeader className="p-0">
                <h1 className="text-title-sm font-bold leading-none">{product.name}</h1>
                {product.brand_name && (
                  <CardDescription className="text-lead text-text-muted pt-2">
                    {product.brand_name}
                  </CardDescription>
                )}
                {product.size && (
                  <CardDescription className="text-lead text-text-muted pt-1">
                    {product.size}
                  </CardDescription>
                )}
              </CardHeader>

              <CardContent className="flex-grow p-0 mt-6 w-full">
                <h2 className="text-lead font-semibold mb-4 text-center">Price Comparison</h2>
                <PriceDisplay prices={product.prices} displayMode="full" />
                {summary && <p className="text-body mt-4 text-center">{summary}</p>}
                {checked && <p className="text-body text-text-muted mt-1 text-center">{checked}</p>}
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
            minProducts={1}
          />
        </div>
      </div>
    </div>
  );
};

export default ProductPage;
