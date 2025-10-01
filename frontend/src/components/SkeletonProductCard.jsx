import React from 'react';
import { Card, Placeholder } from 'react-bootstrap';
import placeholderImage from '../assets/SplitCart_symbol_v2.png';

const SkeletonProductCard = () => {
  return (
    <Card style={{ width: '18rem', minWidth: '18rem', marginRight: '1rem' }}>
      <Card.Img
        variant="top"
        src={placeholderImage}
        style={{
          opacity: 0.3,
          objectFit: 'contain',
          height: '180px' // Approximate height of real product images
        }}
      />
      <Card.Body>
        <Placeholder as={Card.Title} animation="glow">
          <Placeholder xs={8} />
        </Placeholder>
        <Placeholder as={Card.Subtitle} animation="glow">
          <Placeholder xs={5} />
        </Placeholder>
        <Placeholder as={Card.Text} animation="glow">
          <Placeholder xs={4} />
        </Placeholder>
        <Placeholder.Button variant="primary" xs={6} />
      </Card.Body>
    </Card>
  );
};

export default SkeletonProductCard;
