import React, { useState, useEffect } from 'react';
import { Container, Button, Spinner, Alert } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';

const SubstitutionPage = () => {
  const { items } = useShoppingList();
  const [currentProductIndex, setCurrentProductIndex] = useState(0);
  const [substitutionChoices, setSubstitutionChoices] = useState([]); // Stores { originalProductId, selectedSubstituteIds }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Initialize substitutionChoices with original product IDs
    if (items.length > 0 && substitutionChoices.length === 0) {
      setSubstitutionChoices(items.map(item => ({ originalProductId: item.product.id, selectedIds: [item.product.id] })));
    }
  }, [items, substitutionChoices]);

  const currentShoppingListItem = items[currentProductIndex];

  if (items.length === 0) {
    return (
      <Container className="mt-4">
        <Alert variant="info">Your shopping list is empty. Add some products to start splitting your cart!</Alert>
        <Button variant="primary" onClick={() => window.history.back()}>Go Back to Shopping</Button>
      </Container>
    );
  }

  if (!currentShoppingListItem) {
    return (
      <Container className="mt-4">
        <h2>Substitution Complete!</h2>
        <p>You have reviewed all products in your cart.</p>
        {/* TODO: Display summary or navigate to next step */}
        <Button variant="primary">View Final Cart</Button>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2>Split My Cart: Product Substitution</h2>
      <p>Reviewing product {currentProductIndex + 1} of {items.length}</p>

      {loading && <Spinner animation="border" role="status"><span className="visually-hidden">Loading...</span></Spinner>}
      {error && <Alert variant="danger">Error: {error}</Alert>}

      {/* TODO: Display original product and substitutes */}
      <p>Original Product: {currentShoppingListItem.product.name}</p>
      <p>Substitutes will appear here.</p>

      <Button
        variant="primary"
        onClick={() => setCurrentProductIndex(prev => prev + 1)}
        className="mt-3"
      >
        Next Product
      </Button>
    </Container>
  );
};

export default SubstitutionPage;
