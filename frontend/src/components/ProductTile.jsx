import React, { useState, useEffect } from 'react';
import '../css/ProductTile.css';
import '../css/PrimaryProductTile.css';
import logoSymbol from '../assets/splitcart_symbol_v6.png';
import PriceDisplay from './PriceDisplay';
import AddToCartButton from './AddToCartButton';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";


// Logos - moved from ProductCardContent
import aldiLogo from '../assets/ALDI_logo.svg';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';

const companyLogos = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

const ProductTile = ({ product, nearbyStoreIds }) => {
  const [selectedPrice, setSelectedPrice] = useState(null);

  useEffect(() => {
    const prices = product.prices || [];
    const cheapestPrice = prices.find(p => p.is_lowest) || (prices.length > 0 ? prices.reduce((min, p) => p.price < min.price ? p : min, prices[0]) : null);
    setSelectedPrice(cheapestPrice);
  }, [product.prices]);

  const handleImageError = (e) => {
    e.target.onerror = null;
    e.target.src = logoSymbol;
  };

  const handlePriceSelect = (price) => {
    setSelectedPrice(price);
  };

  const prices = product.prices || [];
  const imageUrl = selectedPrice?.image_url || product.image_url || logoSymbol;

  return (
    <Card className="product-card">
        <img
          src={imageUrl} // Use the state-driven image URL
          onError={handleImageError}
          alt={product.name}
        />
        {product.size && (
          <span style={{
            position: 'absolute',
            top: '15px',
            right: '15px',
            backgroundColor: 'white',
            color: 'black',
            padding: '0.2rem 0.4rem',
            borderRadius: '8px',
            fontSize: '0.8rem',
            border: '1px solid var(--colorp2)',
            zIndex: 1,
            fontFamily: 'var(--font-numeric)'
          }}>
            {product.size}
          </span>
        )}
      <CardHeader>
        <CardTitle>{product.name}</CardTitle>
        <CardDescription>
          {product.brand_name && `${product.brand_name} `}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <PriceDisplay 
          prices={prices} 
          variant="product-tile"
          onPriceSelect={handlePriceSelect}
          selectedPrice={selectedPrice}
        />
      </CardContent>
      <CardFooter>
        <div className="actions-container">
          <AddToCartButton product={product} nearbyStoreIds={nearbyStoreIds} />
        </div>
      </CardFooter>
    </Card>
  );
};

export default ProductTile;
