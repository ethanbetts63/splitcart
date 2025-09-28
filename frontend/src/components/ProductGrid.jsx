import React, { useState, useEffect } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import ProductTile from './ProductTile';

const ProductGrid = ({ searchTerm, userLocation }) => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    console.log('Fetching products...');
    let url = '/api/products/';
    const params = new URLSearchParams();

    if (searchTerm) {
      params.append('search', searchTerm);
    }
    if (userLocation && userLocation.postcode && userLocation.radius) {
      params.append('postcode', userLocation.postcode);
      params.append('radius', userLocation.radius);
    }

    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    fetch(url)
      .then(response => {
        console.log('Response:', response);
        return response.json();
      })
      .then(data => {
        console.log('Data:', data);
        if (data && data.results) {
          setProducts(data.results);
        }
      })
      .catch(error => {
        console.error('Error fetching products:', error);
      });
  }, [searchTerm, userLocation]);

  return (
    <Container>
      <Row>
        {products && products.map((product) => (
          <Col key={product.id} sm={6} md={4} lg={3} className="mb-4">
            <ProductTile product={product} />
          </Col>
        ))}
      </Row>
    </Container>
  );
};

export default ProductGrid;