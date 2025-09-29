import React from 'react';
import { Row, Col } from 'react-bootstrap';
import SelectableProductTile from './SelectableProductTile';

const SubstitutesSection = ({ products, selectedOptions, onSelectOption }) => {
  return (
    <Row className="mt-4">
      <Col>
        <Row>
          {products.length > 0 ? (
            products.map(product => (
              <Col key={product.id} sm={6} md={4} lg={3} className="mb-4 p-2">
                <div className="position-relative h-100">
                  <SelectableProductTile
                    product={product}
                    isSelected={selectedOptions.includes(product.id)}
                    onSelect={onSelectOption}
                  />
                  {product.is_original ? (
                    <div 
                      className="position-absolute top-0 start-0 bg-primary text-white p-1"
                      style={{ fontSize: '0.75rem', borderTopLeftRadius: '0.25rem' }}
                    >
                      Original Product
                    </div>
                  ) : product.level_description && (
                    <div 
                      className="position-absolute top-0 start-0 bg-info text-white p-1"
                      style={{ fontSize: '0.75rem', borderTopLeftRadius: '0.25rem' }}
                    >
                      {product.level_description}
                    </div>
                  )}
                </div>
              </Col>
            ))
          ) : (
            <p>No substitutes found for this product.</p>
          )}
        </Row>
      </Col>
    </Row>
  );
};

export default SubstitutesSection;
