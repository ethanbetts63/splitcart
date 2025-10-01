import React, { useState, useEffect } from 'react';
import { Container, Button, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import SubstitutesSection from '../components/SubstitutesSection';
import LocationSetupModal from '../components/LocationSetupModal'; // To get userLocation
import { useNavigate } from 'react-router-dom';

export const SubstitutionPage = () => {
  const { items, substitutes, updateSubstitutionChoices, nearbyStoreIds } = useShoppingList();
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

  const handleNextProduct = () => {
    if (!currentItem) return;

    const allAvailableProducts = [currentItem.product, ...(currentSubstitutes || [])];
    const selectedProducts = allAvailableProducts.filter(p => selectedOptions.includes(p.id));
    
    updateSubstitutionChoices(currentItem.product.id, selectedProducts);
    setCurrentProductIndex(prev => prev + 1);
  };

  const handleViewFinalCart = () => {
    const formattedCart = items.map(item => ({
      product_id: item.product.id,
      quantity: item.quantity || 1,
      // Note: The backend will need to handle the logic for chosen substitutes.
      // This simplified format just sends the primary items.
    }));

    navigate('/final-cart', { state: { cart: formattedCart, store_ids: nearbyStoreIds } });
  };

  if (items.length === 0) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="info">Your shopping list is empty. Add some products to start splitting your cart!</Alert>
        <Button variant="primary" onClick={() => navigate('/')}>Go Back to Shopping</Button>
      </Container>
    );
  }

  if (!currentItem) {
    return (
      <Container fluid className="mt-4">
        <h2>Substitution Complete!</h2>
        <p>You have reviewed all products in your cart.</p>
        <Button variant="primary" onClick={handleViewFinalCart}>View Final Cart</Button>
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
        onClick={handleNextProduct}
        className="mt-3"
      >
        Next Product
      </Button>
    </Container>
  );
};

  if (items.length === 0) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="info">Your shopping list is empty. Add some products to start splitting your cart!</Alert>
        <Button variant="primary" onClick={() => window.history.back()}>Go Back to Shopping</Button>
      </Container>
    );
  }

  if (!currentShoppingListSlot) {
    return (
      <Container fluid className="mt-4">
        <h2>Substitution Complete!</h2>
        <p>You have reviewed all products in your cart.</p>
        <Button variant="primary" onClick={handleViewFinalCart}>View Final Cart</Button>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <h2>Product Substitution</h2>
      <p className="text-muted mb-4">
        Please select all items you are willing to consider as substitutes for the original product. 
        The more options you provide, the greater the flexibility the algorithm has to optimize your total cart cost. 
        The system aims for the lowest overall cart price, which might involve selecting a seemingly more expensive 
        individual substitute if it leads to greater savings across your entire shopping list.
      </p>

      <Button
        variant="primary"
        onClick={handleNextProduct}
        className="mt-3"
      >
        Next Product
      </Button>

      <SubstitutesSection 
        products={[{ ...currentShoppingListSlot[0].product, is_original: true }, ...substitutes]}
        selectedOptions={selectedOptions}
        onSelectOption={handleSelectOption}
      />
    </Container>
  );