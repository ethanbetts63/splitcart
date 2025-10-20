import { useShoppingList } from '@/context/ShoppingListContext';
import TrolleyItemTile from '@/components/TrolleyItemTile';
import NextButton from '@/components/NextButton'; // Import NextButton

interface TrolleyPageProps {
  onOpenChange: (open: boolean) => void;
}

const TrolleyPage: React.FC<TrolleyPageProps> = ({ onOpenChange }) => {
  const { items, cartTotal } = useShoppingList();

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lg font-semibold">My Trolley ({cartTotal} items)</h3>
        {items.length > 0 && (
          <NextButton onAfterNavigate={() => onOpenChange(false)} />
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