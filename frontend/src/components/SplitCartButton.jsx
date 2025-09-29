import React from 'react';
import { Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const SplitCartButton = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/split-cart');
  };

  return (
    <Button style={{ backgroundColor: '#1CC3B9', color: 'white' }} onClick={handleClick} size="lg">
      Split My Cart!
    </Button>
  );
};

export default SplitCartButton;