import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useStoreList } from '../context/StoreListContext';
import ProductTile from '../components/ProductTile';
import CartItemTile from '../components/CartItemTile';
import LoadingSpinner from '../components/LoadingSpinner';
import type { CartSubstitution } from '../types';
import { FAQ } from "../components/FAQ";
import sizeDoesntMatterImage from "../assets/size_doesnt_matter.webp";
import useMediaQuery from '../hooks/useMediaQuery';
import { ArrowLeft, ArrowRight } from 'lucide-react';

const substitutesFaqs = [
  {"question": "Should I consider price?", "answer": "Short answer is no. Just pick anything that you would be willing to have \"instead of\" the original. Long answer is very mathematical but suffice to say that the algorithm will often unexpectedly pick very expensive isolated items because it allows it to lower the overall cost in other areas."},
  {"question": "Why can I adjust the quantity?", "answer": "If you're original item was 1 liter of milk and the substitute we offered you was 500ml of milk, that wouldn't make sense. So that's why you can adjust the quantity to say that yes I would be willing to have two 500ml bottles of milk instead of the liter if it was cheaper."},
  {"question": "How many substitutes should I pick?", "answer": "As many as possible. The more you pick the more you're likely to save."},
  {"question": "Can I split without substitutes?", "answer": "Yes, but you're missing out. Even when you split with substitutes we will still show you what you would have saved without using substitutes so you can decide for yourself."},
  {"question": "No, but does it really matter?", "answer": "Subsitutes are our secret sauce. No other price comaparison website has thought of it. If you were actually in a store you would never just consider one product. You would probably debate between a few items on any shelf. That's what we are replicating and your hard work pays dividends."}
];

const SubstitutionPage = () => {
  const navigate = useNavigate();
  const { currentCart, updateCartItemSubstitution, optimizeCurrentCart, isFetchingSubstitutions } = useCart();
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const { currentStoreListId } = useStoreList();

  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const itemsToReview = currentCart?.items.filter(item => item.substitutions && item.substitutions.length > 0) || [];

  useEffect(() => {
    console.log('[SubstitutionPage] skip-check effect fired:', {
      isFetchingSubstitutions,
      hasCart: !!currentCart,
      itemsToReview: itemsToReview.length,
      allItems: currentCart?.items.map(i => ({ id: i.id, subs: i.substitutions?.length ?? 0 })),
    });
    if (!isFetchingSubstitutions && currentCart && itemsToReview.length === 0) {
      console.log('[SubstitutionPage] skipping to optimize — no items with substitutions');
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
      await updateCartItemSubstitution(currentItem.id, sub.id, false, 1);
    } else {
      await updateCartItemSubstitution(currentItem.id, sub.id, sub.is_approved, newQuantity);
    }
  };

  const handleOptimizeAndNavigate = async () => {
    if (!currentCart || !currentStoreListId) return;
    setIsLoading(true);
    try {
      const results = await optimizeCurrentCart(currentStoreListId);
      if (results) {
        navigate('/final-cart');
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      console.error(error);
      setIsLoading(false);
    }
  };

  const handleSkipSubstitutions = async () => {
    if (!currentCart || !currentStoreListId) return;
    setIsLoading(true);
    try {
      const results = await optimizeCurrentCart(currentStoreListId);
      if (results) {
        navigate('/final-cart');
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      console.error(error);
      setIsLoading(false);
    }
  };

  const handleApproveAllAndNext = async () => {
    if (!currentItem) return;
    setIsLoading(true);
    try {
      for (const sub of currentSubstitutes) {
        if (!sub.is_approved) {
          await updateCartItemSubstitution(currentItem.id, sub.id, true, sub.quantity);
        }
      }
      if (currentItemIndex < itemsToReview.length - 1) {
        setCurrentItemIndex(currentItemIndex + 1);
      } else {
        await handleOptimizeAndNavigate();
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || isFetchingSubstitutions) return <LoadingSpinner />;
  if (itemsToReview.length === 0) return <LoadingSpinner />;

  const isLastItem = currentItemIndex === itemsToReview.length - 1;
  const progressPercent = (currentItemIndex / itemsToReview.length) * 100;
  const approvedCount = currentSubstitutes.filter(s => s.is_approved).length;

  return (
    <div className="container mx-auto px-4 py-6">

      {/* Primary Nav */}
      <div className="flex items-center justify-between gap-4 mb-3">
        <button
          onClick={handleBack}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold border border-gray-300 bg-white rounded-lg hover:border-gray-900 hover:text-gray-900 transition-colors duration-150"
        >
          <ArrowLeft className="h-4 w-4" />
          {currentItemIndex === 0 ? 'Home' : 'Back'}
        </button>

        <div className="text-center">
          <h1 className="text-xl font-bold text-gray-900">Approve Substitutes</h1>
          <p className="text-sm text-gray-400">Item {currentItemIndex + 1} of {itemsToReview.length}</p>
        </div>

        <button
          onClick={handleNext}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-bold bg-yellow-300 hover:bg-yellow-400 active:bg-yellow-500 text-black rounded-lg transition-colors duration-150"
        >
          {isLastItem ? 'Split my Cart!' : 'Next'}
          {!isLastItem && <ArrowRight className="h-4 w-4" />}
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div
            className="bg-yellow-400 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Secondary Actions */}
      <div className="flex items-center justify-between mb-5">
        <button
          onClick={handleSkipSubstitutions}
          className="text-sm text-gray-400 hover:text-gray-700 underline underline-offset-2 transition-colors"
        >
          Skip all substitutions
        </button>
        <button
          onClick={handleApproveAllAndNext}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold border border-gray-300 bg-white rounded-lg hover:border-gray-900 hover:text-gray-900 transition-colors duration-150"
        >
          Approve All & {isLastItem ? 'Split' : 'Next'}
        </button>
      </div>

      {/* Main Panel */}
      <div className="bg-gray-50 rounded-xl p-5">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Original Product */}
          <div>
            <h2 className="text-base font-bold mb-4 text-center">
              <span className="italic bg-yellow-300 px-1 py-0.5 rounded text-black">Original Product</span>
            </h2>
            {isDesktop ? (
              <div className="w-[240px] mx-auto">
                <ProductTile product={currentItem.product} />
              </div>
            ) : (
              <CartItemTile product={currentItem.product} context="cart" hideApprovedSubstitutions={true} />
            )}
          </div>

          {/* Substitutes */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold">
                <span className="italic bg-yellow-300 px-1 py-0.5 rounded text-black">Substitutes</span>
              </h2>
              {approvedCount > 0 && (
                <span className="text-xs font-semibold text-green-600 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">
                  {approvedCount} approved
                </span>
              )}
            </div>
            <div className="h-[480px] overflow-y-auto rounded-xl border border-gray-200 bg-white p-3 space-y-3">
              {currentSubstitutes.map(sub => {
                if (sub.substituted_product.prices && sub.substituted_product.prices.length > 0) {
                  return (
                    <CartItemTile
                      key={sub.id}
                      cartSubstitution={sub}
                      onApprove={handleApprove}
                      onQuantityChange={handleQuantityChange}
                      context="substitution"
                    />
                  );
                }
                return null;
              })}
            </div>
          </div>

        </div>
      </div>

      {/* FAQ */}
      <div className="mt-12">
        <FAQ
          title="Why substitution?"
          faqs={substitutesFaqs}
          imageSrc={sizeDoesntMatterImage}
          imageAlt="Scale balancing small bottles with many dollar signs against a large bottle with one dollar sign, with text 'Size doesn't matter, value does.'"
        />
      </div>

    </div>
  );
};

export default SubstitutionPage;
