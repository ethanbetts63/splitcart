import React, { useState, useEffect } from 'react';
import { Container, Button, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import SubstitutesSection from '../components/SubstitutesSection';
import LocationSetupModal from '../components/LocationSetupModal'; // To get userLocation
import { useNavigate } from 'react-router-dom';

const SubstitutionPage = () => {
  const { items, substitutes, selections, updateSubstitutionChoices, nearbyStoreIds } = useShoppingList();
  const navigate = useNavigate();
  const [currentProductIndex, setCurrentProductIndex] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState([]);

  const currentItem = items[currentProductIndex];
  const currentSubstitutes = currentItem ? substitutes[currentItem.product.id] : undefined;

  // Effect to auto-advance if no substitutes are available for the current item
  useEffect(() => {
    if (currentItem && currentSubstitutes && currentSubstitutes.length === 0) {
      // No substitutes, so we "choose" the original product and move on.
      updateSubstitutionChoices(currentItem.product.id, [currentItem.product]);
      setCurrentProductIndex(prev => prev + 1);
    }
  }, [currentItem, currentSubstitutes, updateSubstitutionChoices]);

  // Effect to initialize selected options when the product changes
  useEffect(() => {
    if (currentItem) {
      // For now, we just pre-select the original item.
      // The logic for persisting choices across sessions would go here.
      setSelectedOptions([currentItem.product.id]);
    }
  }, [currentItem]);


  const handleSelectOption = (productId) => {
    setSelectedOptions(prevSelected => {
      if (productId === currentItem.product.id) return prevSelected; // Prevent deselecting original
      return prevSelected.includes(productId)
        ? prevSelected.filter(id => id !== productId)
        : [...prevSelected, productId];
    });
  };

  const isLastProduct = currentProductIndex === items.length - 1;

  const handleNextProduct = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));
    
    updateSubstitutionChoices(currentItem.product.id, selectedProducts);
    setCurrentProductIndex(prev => prev + 1);
  };

  const handleFinishAndSplit = () => {
    if (!currentItem) return;

    // First, save the choices for the current (last) item
    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));
    updateSubstitutionChoices(currentItem.product.id, selectedProducts);

    // Now, navigate immediately. We need to ensure the state update from
    // updateSubstitutionChoices is available, so we manually build the final cart data here.
    const finalSelections = { ...selections, [currentItem.product.id]: selectedProducts };

    const formattedCart = items.map(item => {
      const originalProductId = item.product.id;
      const prods = finalSelections[originalProductId];
      if (prods && prods.length > 0) {
        return prods.map(p => ({ product_id: p.id, quantity: item.quantity }));
      }
      return [{ product_id: originalProductId, quantity: item.quantity || 1 }];
    });

    navigate('/final-cart', { state: { cart: formattedCart, store_ids: nearbyStoreIds } });
  };

  // This page is now effectively removed from the primary user flow.
  if (!currentItem && items.length > 0) {
    return (
      <Container fluid className="mt-4">
        <h2>Substitution Complete!</h2>
        <p>You have reviewed all products in your cart.</p>
        <Button variant="primary" onClick={() => navigate('/final-cart', { state: { cart: [], store_ids: nearbyStoreIds } })}>View Final Cart</Button>
      </Container>
    );
  }

  // Show loading spinner if substitutes for the current item are not yet fetched
  if (currentSubstitutes === undefined) {
    return <Container className="text-center my-5"><Spinner animation="border" /></Container>;
  }

  return (
    <Container fluid className="mt-4">
      <h2>Product Substitution</h2>
      <p className="text-muted mb-4">
        Reviewing substitutes for: <strong>{currentItem.product.name}</strong>
      </p>

      <SubstitutesSection 
        products={[{ ...currentItem.product, is_original: true }, ...(currentSubstitutes || [])]}
        selectedOptions={selectedOptions}
        onSelectOption={handleSelectOption}
      />

      <Button
        variant="primary"
        onClick={isLastProduct ? handleFinishAndSplit : handleNextProduct}
        className="mt-3"
      >
        {isLastProduct ? 'Split My Cart' : 'Next Product'}
      </Button>
    </Container>
  );
};

export default SubstitutionPage;
