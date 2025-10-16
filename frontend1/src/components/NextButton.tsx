import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useShoppingList } from '@/context/ShoppingListContext';
import { useSubstitutions } from '@/context/SubstitutionContext';
import { Button } from '@/components/ui/button';

interface NextButtonProps {
  onAfterNavigate?: () => void; // Optional callback
}

const NextButton: React.FC<NextButtonProps> = ({ onAfterNavigate }) => {
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
    <Button onClick={handleNextClick} className="bg-green-500 hover:bg-green-600">
      Next
    </Button>
  );
};

export default NextButton;
