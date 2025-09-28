import React from 'react';
import { Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const SplitCartButton = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/split-cart');
  };

  return (
    <Button variant="info" onClick={handleClick} className="ms-2">
      Split My Cart!
    </Button>
  );
};

export default SplitCartButton;
