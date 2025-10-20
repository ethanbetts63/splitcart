import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface NextButtonProps {
  onAfterNavigate?: () => void; // Optional callback
  className?: string;
}

const NextButton: React.FC<NextButtonProps> = ({ onAfterNavigate, className }) => {
  const navigate = useNavigate();
  const { items } = useShoppingList();
  const { setItemsToReview, substitutes } = useSubstitutions();

  const handleNextClick = () => {
    const itemsWithSubstitutes = items.filter(item => substitutes[item.product.id] && substitutes[item.product.id].length > 0);
    if (itemsWithSubstitutes.length > 0) {
      setItemsToReview(itemsWithSubstitutes.map(item => item.product));
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