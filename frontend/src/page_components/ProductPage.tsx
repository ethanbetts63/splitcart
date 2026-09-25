import type { Product } from '../types';
import PriceDisplay from '../components/PriceDisplay';
import AddToCartButton from '../components/AddToCartButton';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/common/card';
import { ProductCarousel } from '../components/ProductCarousel';
import { assetSrc } from '@/lib/assets';
import { notFound } from 'next/navigation';

type ProductPageProps = {
  product: Product | null;
};

/**
 * No structured data here, deliberately.
 *
 * `/product` is robots-disallowed -- see `app/product/[slug]/page.tsx` and
 * `DISALLOWED_ROUTES` in `app/robots.txt/route.ts`. A disallowed page is never
 * fetched, so JSON-LD on it is never parsed, and the block that used to sit
 * here was inert in exactly the way that route's own comment describes.
 *
 * It was not harmlessly inert. It was a raw <script type="application/ld+json">
 * built with plain JSON.stringify over scraped supermarket product names, so a
 * name containing </script would have closed the element early and handed what
 * followed to the browser as markup. It also published SplitCart's Django
 * primary key as `sku`, minted a fresh anonymous Organization per price instead
 * of referencing the canonical retailer nodes, and hard-coded a second spelling
 * of the site origin beside `lib/siteConfig.ts`.
 *
 * If `/product` is ever removed from the disallow list, build the graph with
 * `buildProductItemListSchema`/`buildRetailerSchemas` from `lib/seo.ts` and
 * emit it through `StructuredDataScript`, which escapes `<`. Do not restore
 * what was here.
 */
const ProductPage = ({ product }: ProductPageProps) => {
  if (!product) notFound();

  const imageUrl = product.image_url || assetSrc(fallbackImage);

  return (
    <div className="site-shell py-4">
      <div className="max-w-5xl mx-auto">
        <Card className="overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
            {/* Image Column */}
            <div className="aspect-square w-full overflow-hidden">
              <img src={imageUrl} alt={product.name} className="h-full w-full object-cover" />
            </div>

            {/* Details Column */}
            <div className="flex flex-col p-2">
              <CardHeader className="p-0">
                <CardTitle className="text-title-sm font-bold">{product.name}</CardTitle>
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
                <h3 className="text-lead font-semibold mb-4 text-center">Price Comparison</h3>
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
            minProducts={1}
          />
        </div>
      </div>
    </div>
  );
};

export default ProductPage;
