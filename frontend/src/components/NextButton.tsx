import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '@/context/CartContext';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface NextButtonProps {
  onAfterNavigate?: () => void; // Optional callback
  className?: string;
}

const NextButton: React.FC<NextButtonProps> = ({ onAfterNavigate, className }) => {
  const navigate = useNavigate();
  const { currentCart } = useCart();

  // this should user item.substitutions to determine where to go next it should use the page that the user is on.
  const handleNextClick = () => {
    const itemsWithSubstitutes = currentCart?.items.filter(item => 
      item.substitutions && item.substitutions.length > 0
    ) || [];

    if (itemsWithSubstitutes.length > 0) {
      navigate('/substitutions');
    } else {
      navigate('/final-cart');
    }

    if (onAfterNavigate) {
      onAfterNavigate();
    }
  };

  return (
    <Button onClick={handleNextClick} className={cn("bg-green-500 hover:bg-green-600", className)}>
      Next
    </Button>
  );
};

export default NextButton;