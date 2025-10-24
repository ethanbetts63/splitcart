import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '@/context/CartContext';
import { useStoreList } from '@/context/StoreListContext';
import ProductTile from '@/components/ProductTile';
import CartItemTile from '@/components/CartItemTile';
import { Button } from '@/components/ui/button';
import { optimizeCartAPI } from '@/services/SubstitutionApi';
import LoadingSpinner from '@/components/LoadingSpinner';
import type { Product, CartSubstitution } from '@/types';
import { Badge } from "@/components/ui/badge";
import { BadgeCheckIcon } from 'lucide-react';
import { FaqImageSection } from "../components/FaqImageSection";
import kingKongImage from "../assets/king_kong.png";

const SubstitutionPage = () => {
  const navigate = useNavigate();
  const { currentCart, setOptimizationResult, updateCartItemSubstitution, removeCartItemSubstitution } = useCart();
  const { selectedStoreIds } = useStoreList();

  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const itemsToReview = currentCart?.items.filter(item => item.substitutions && item.substitutions.length > 0) || [];
  const currentItem = itemsToReview[currentItemIndex];
  const currentSubstitutes = currentItem ? currentItem.substitutions : [];

  const handleNext = () => {
    if (currentItemIndex < itemsToReview.length - 1) {
      setCurrentItemIndex(currentItemIndex + 1);
    } else {
      handleOptimizeAndNavigate();
    }
  };

  const handleBack = () => {
    if (currentItemIndex > 0) {
      setCurrentItemIndex(currentItemIndex - 1);
    } else {
      navigate('/');
    }
  };

  const handleApprove = async (sub: CartSubstitution) => {
    if (!currentItem) return;
    await updateCartItemSubstitution(currentItem.id, sub.id, !sub.is_approved, sub.quantity);
  };

  const handleQuantityChange = async (sub: CartSubstitution, newQuantity: number) => {
    if (!currentItem) return;
    if (newQuantity <= 0) {
      // If quantity goes to 0, set is_approved to false
      await updateCartItemSubstitution(currentItem.id, sub.id, false, 1); // Set quantity to 1 if unapproved
    } else {
      await updateCartItemSubstitution(currentItem.id, sub.id, sub.is_approved, newQuantity);
    }
  };

  const handleOptimizeAndNavigate = async () => {
    if (!currentCart) return;

    setIsLoading(true);

    try {
      // Assuming optimizeCartAPI now takes only cartId
      const results = await optimizeCartAPI(currentCart.id);
      setOptimizationResult(results);
      navigate('/final-cart');
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipSubstitutions = async () => {
    if (!currentCart) return;

    setIsLoading(true);

    try {
      // Assuming optimizeCartAPI now takes only cartId
      const results = await optimizeCartAPI(currentCart.id);
      setOptimizationResult(results);
      navigate('/final-cart');
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveAllAndNext = async () => {
    if (!currentItem) return;
    setIsLoading(true); // Set loading for the batch update
    try {
      for (const sub of currentSubstitutes) {
        if (!sub.is_approved) { // Only update if not already approved
          await updateCartItemSubstitution(currentItem.id, sub.id, true, sub.quantity);
        }
      }
      // After approving all, move to next or optimize
      if (currentItemIndex < itemsToReview.length - 1) {
        setCurrentItemIndex(currentItemIndex + 1);
      } else {
        await handleOptimizeAndNavigate(); // Call the simplified optimize
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!currentItem) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold mb-4">No Substitutes to Review</h2>
        <p className="mb-4">None of the items in your cart currently have substitute options available.</p>
        <Button onClick={() => handleOptimizeAndNavigate()}>Proceed to Final Cart</Button>
      </div>
    );
  }

  const isLastItem = currentItemIndex === itemsToReview.length - 1;

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-3 items-center mb-4">
        <div className="justify-self-start flex items-center gap-2">
          <Button onClick={handleBack} className="bg-red-500 text-white">
            {currentItemIndex === 0 ? 'Home' : 'Back'}
          </Button>
          <Button onClick={handleSkipSubstitutions} variant="outline">
            Skip Substitutions
          </Button>
        </div>
        <h1 className="text-2xl font-bold justify-self-center">Product Substitution</h1>
        <div className="justify-self-end flex items-center gap-2">
          <Button onClick={handleApproveAllAndNext} variant="outline">
            Approve All
          </Button>
          <Button onClick={handleNext} className="bg-blue-500 text-white">
            {isLastItem ? 'Split my Cart!' : 'Next'}
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Original Product</h2>
          <div className="w-[240px] mx-auto relative">
            <Badge variant="secondary" className="absolute top-2 left-2 z-10 bg-green-500 text-white dark:bg-green-600">
              <BadgeCheckIcon className="w-4 h-4 mr-1" />
              Original Product
            </Badge>
            <ProductTile product={currentItem.product} />
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Substitutes</h2>
          <div className="h-[480px] overflow-y-auto border rounded-md p-4 space-y-4">
            {currentSubstitutes.map(sub => {
              return (
                <CartItemTile 
                  key={sub.id} 
                  cartSubstitution={sub} // Pass the CartSubstitution object directly
                  onApprove={handleApprove} 
                  onQuantityChange={handleQuantityChange}
                  context="substitution"
                />
              )
            })}
          </div>
        </div>
      </div>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section>
            <FaqImageSection
              title="Why substitution?"
              page="substitutes"
              imageSrc={kingKongImage}
              imageAlt="King Kong swatting at discount planes"
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default SubstitutionPage;