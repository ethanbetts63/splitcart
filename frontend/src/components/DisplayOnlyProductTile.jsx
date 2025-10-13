
import React from 'react';
import placeholderImage from '../assets/splitcart_symbol_v6.png';
import './../css/SmallProductTile.css'; // Reuse the same CSS for a consistent look
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const DisplayOnlyProductTile = ({ item }) => {

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = placeholderImage;
  };

  return (
    <Card className="small-product-tile" style={{ marginBottom: '0.25rem' }}>
      <CardHeader>
        <div className="row-1">
          <img src={item.image_url || placeholderImage} onError={handleImageError} alt={item.name} className="product-image" />
          <div className="product-details">
            <CardTitle>{item.name}</CardTitle>
            <div>
              <small className="text-muted">{item.brand}</small>
              <span className="product-size">{item.size}</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="row-2">
          <div>
              <span style={{ fontFamily: 'var(--font-numeric)' }}>${item.price.toFixed(2)}</span>
          </div>
          <div>
              <span style={{ fontFamily: 'var(--font-numeric)' }}>Qty: {item.quantity}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DisplayOnlyProductTile;
