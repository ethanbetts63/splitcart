import React from 'react';
import { Row, Col } from 'react-bootstrap';
import SelectableProductTile from './SelectableProductTile';

const SubstitutesSection = ({ originalProduct, substitutes, selectedOptions, onSelectOption }) => {
  const searchButtonStyle = {
    border: '2px solid #1CC3B9',
    borderRadius: '0.25rem',
    padding: '1rem',
    boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
  };

  return (
    <Row className="mt-4">
      {/* Original Product */}
      <Col md={4} className="mb-4">
        <div style={searchButtonStyle}>
          <h5>Original Product</h5>
          <SelectableProductTile
            product={originalProduct}
            isSelected={selectedOptions.includes(originalProduct.id)}
            onSelect={onSelectOption}
          />
        </div>
      </Col>

      {/* Substitutes Grid */}
      <Col md={8}>
        <h5>Substitutes</h5>
        <Row>
          {substitutes.length > 0 ? (
            substitutes.map(sub => (
              <Col key={sub.id} sm={6} md={4} lg={4} className="mb-4 p-2">
                <div className="position-relative">
                  <SelectableProductTile
                    product={sub}
                    isSelected={selectedOptions.includes(sub.id)}
                    onSelect={onSelectOption}
                  />
                  {sub.level_description && (
                    <div 
                      className="position-absolute top-0 start-0 bg-info text-white p-1"
                      style={{ fontSize: '0.75rem', borderTopLeftRadius: '0.25rem' }}
                    >
                      {sub.level_description}
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
