import React from 'react';
import { Container, Row, Col, Button, Spinner } from 'react-bootstrap';
import ProductTile from './ProductTile';

const ProductGrid = ({ products, onLoadMore, hasMorePages, isLoadingMore, title }) => {

  return (
    <Container fluid>
      {title && <h5 className="mb-3">{title}</h5>}
      <Row>
        {products.length > 0 ? (
          products.map((product) => (
            <Col key={product.id} sm={6} md={4} lg={3} className="mb-4">
              <ProductTile product={product} />
            </Col>
          ))
        ) : (
          <Col className="text-center my-5">No products found.</Col>
        )}
      </Row>

      {hasMorePages && (
        <div className="text-center my-4">
          <Button onClick={onLoadMore} disabled={isLoadingMore}>
            {isLoadingMore ? <Spinner animation="border" size="sm" /> : 'Load More'}
          </Button>
        </div>
      )}
    </Container>
  );
};

export default ProductGrid;