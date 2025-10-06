import React from 'react';
import { Card } from 'react-bootstrap';
import placeholderImage from '../assets/trolley_v3.webp';

const ProductCardContent = ({ product }) => {
  console.log("ProductCardContent received product:", product); // Debug log

  const getCompanyColor = (companyName) => {
    switch (companyName.toLowerCase()) {
      case 'coles': return 'red';
      case 'woolworths': return 'green';
      case 'aldi': return 'blue';
      case 'iga': return 'orange';
      default: return 'black';
    }
  };

  if (!product) {
    console.log("ProductCardContent received null or undefined product."); // Debug log
    return null; // Don't render if no product
  }

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = placeholderImage;
  };

  return (
    <>
      <Card.Img 
        variant="top" 
        src={product.image_url || placeholderImage} 
        onError={handleImageError}
      />
      <Card.Body>
        <Card.Title>{product.name}</Card.Title>
        {product.brand_name && <Card.Subtitle className="mb-2 text-muted">{product.brand_name}</Card.Subtitle>}
        {product.size && <Card.Text className="text-muted">Size: {product.size}</Card.Text>}
        <Card.Text as="div">
          {product.prices && product.prices.map(priceData => {
            const companyColor = getCompanyColor(priceData.company);
            const companyNameStyle = {
              color: companyColor,
              fontWeight: 'bold',
            };
            const priceValueStyle = {
              color: priceData.is_lowest ? 'green' : 'black',
              fontWeight: priceData.is_lowest ? 'bold' : 'normal',
            };
            return (
              <div key={priceData.company}>
                <span style={companyNameStyle}>{priceData.company}</span>: <span style={priceValueStyle}>${priceData.price_display}</span>
              </div>
            );
          })}
        </Card.Text>
      </Card.Body>
    </>
  );
};

export default ProductCardContent;
