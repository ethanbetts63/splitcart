import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useStoreList } from '../context/StoreListContext';
import ProductTile from '../components/ProductTile';
import CartItemTile from '../components/CartItemTile';
import { Button } from '../components/ui/button';
import { optimizeCartAPI } from '../services/cartOptimization.api';
import LoadingSpinner from '../components/LoadingSpinner';
import type { CartSubstitution } from '../types';
import { Badge } from "../components/ui/badge";
import { BadgeCheckIcon } from 'lucide-react';
import { FAQ } from "../components/FAQ";
import sizeDoesntMatterImage from "../assets/size_doesnt_matter.webp";
import useMediaQuery from '../hooks/useMediaQuery';

const SubstitutionPage = () => {
  const navigate = useNavigate();
  const { currentCart, setOptimizationResult, updateCartItemSubstitution, isFetchingSubstitutions } = useCart();
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  useStoreList(); // Call hook to ensure context is available, but don't destructure

  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const itemsToReview = currentCart?.items.filter(item => item.substitutions && item.substitutions.length > 0) || [];

  useEffect(() => {
    // Automatically navigate if there are no substitutes to review after loading is complete.
    if (!isFetchingSubstitutions && currentCart && itemsToReview.length === 0) {
      handleOptimizeAndNavigate();
    }
  }, [isFetchingSubstitutions, currentCart, itemsToReview.length]);

  const currentItem = itemsToReview[currentItemIndex];
  const currentSubstitutes = currentItem?.substitutions || [];

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
      // setIsLoading(false); // Removed to prevent flash before navigation
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

  if (isLoading || isFetchingSubstitutions) {
    return <LoadingSpinner />;
  }

  // If there are no items to review, we are in the process of navigating away.
  // Show a loading spinner to avoid rendering the rest of the page with no data.
  if (itemsToReview.length === 0) {
    return <LoadingSpinner />;
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
      <div className="bg-muted p-6 rounded-lg border">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-bold mb-4 text-center">
            <span className="italic bg-yellow-300 px-0.5 py-1 rounded text-black">Original Product</span>
          </h2>
          {isDesktop ? (
            <div className="w-[240px] mx-auto relative">
              <Badge variant="secondary" className="absolute top-2 left-2 z-10 bg-green-500 text-white dark:bg-green-600">
                <BadgeCheckIcon className="w-4 h-4 mr-1" />
                Original Product
              </Badge>
              <ProductTile product={currentItem.product} />
            </div>
          ) : (
            <CartItemTile product={currentItem.product} context="cart" hideApprovedSubstitutions={true} />
          )}
        </div>
        <div>
          <h2 className="text-xl font-bold mb-4 text-center">
            <span className="italic bg-yellow-300 px-0.5 py-1 rounded text-black">Substitutes</span>
          </h2>
          <div className="h-[480px] overflow-y-auto border rounded-md p-4 space-y-4">
            {currentSubstitutes.map(sub => {
              // Only render the substitute if it has prices
              if (sub.substituted_product.prices && sub.substituted_product.prices.length > 0) {
                return (
                  <CartItemTile 
                    key={sub.id} 
                    cartSubstitution={sub} // Pass the CartSubstitution object directly
                    onApprove={handleApprove} 
                    onQuantityChange={handleQuantityChange}
                    context="substitution"
                  />
                )
              }
              return null; // Do not render if no prices
            })}
          </div>
        </div>
      </div>
      </div>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-8">
          <section>
            <FAQ
              title="Why substitution?"
              page="substitutes"
              imageSrc={sizeDoesntMatterImage}
              imageAlt="Scale balancing small bottles with many dollar signs against a large bottle with one dollar sign, with text 'Size doesn't matter, value does.'"
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default SubstitutionPage;