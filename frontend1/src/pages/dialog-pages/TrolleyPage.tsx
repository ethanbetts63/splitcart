import { useShoppingList } from '@/context/ShoppingListContext';
import TrolleyItemTile from '@/components/TrolleyItemTile';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

import { useSubstitutions } from '@/context/SubstitutionContext';

interface TrolleyPageProps {
  onOpenChange: (open: boolean) => void;
}

const TrolleyPage: React.FC<TrolleyPageProps> = ({ onOpenChange }) => {
  const { items, cartTotal } = useShoppingList();
  const { setItemsToReview, substitutes } = useSubstitutions();
  const navigate = useNavigate();

  const handleNext = () => {
    const itemsWithSubstitutes = items.filter(item => substitutes[item.product.id] && substitutes[item.product.id].length > 0);
    if (itemsWithSubstitutes.length > 0) {
      setItemsToReview(itemsWithSubstitutes.map(item => item.product));
      navigate('/substitutions');
    } else {
      navigate('/final-cart');
    }
    onOpenChange(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lg font-semibold">My Trolley ({cartTotal} items)</h3>
        {items.length > 0 && (
          <Button onClick={handleNext} className="bg-green-500 hover:bg-green-600">Next</Button>
        )}
      </div>
      <div className="flex-grow overflow-y-auto p-4">
        {items.length > 0 ? (
          <div className="flex flex-col gap-4">
            {items.map(item => (
              <TrolleyItemTile key={item.product.id} product={item.product} context="trolley" />
            ))}
          </div>
        ) : (
          <div className="text-center text-muted-foreground pt-8">
            <p>Your trolley is empty.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrolleyPage;
