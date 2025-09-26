import React, { useState, useEffect } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import ProductTile from './ProductTile';

const ProductGrid = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch('/api/products/');
        const data = await response.json();
        setProducts(data.results);
      } catch (error) {
        console.error('Error fetching products:', error);
      }
    };

    fetchProducts();
  }, []);

  return (
    <Container>
      <Row>
        {products.map((product) => (
          <Col key={product.id} sm={6} md={4} lg={3} className="mb-4">
            <ProductTile product={product} />
          </Col>
        ))}
      </Row>
    </Container>
  );
};

export default ProductGrid;