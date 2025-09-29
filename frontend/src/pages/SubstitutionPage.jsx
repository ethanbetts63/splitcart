import React, { useState, useEffect } from 'react';
import { Container, Button, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import SelectableProductTile from '../components/SelectableProductTile'; // Use SelectableProductTile
import LocationSetupModal from '../components/LocationSetupModal'; // To get userLocation

const SubstitutionPage = () => {
  const { items } = useShoppingList();
  const [currentProductIndex, setCurrentProductIndex] = useState(0);
  const [substitutionChoices, setSubstitutionChoices] = useState([]); // Stores { originalProductId, selectedSubstituteIds }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [substitutes, setSubstitutes] = useState([]);
  const [userLocation, setUserLocation] = useState(null); // { postcode: 'XXXX', radius: Y }
  const [selectedOptions, setSelectedOptions] = useState([]); // State for current product's selections

  // Load user location from localStorage
  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      setUserLocation(JSON.parse(savedLocation));
    }
  }, []);

  useEffect(() => {
    // Initialize substitutionChoices with original product IDs
    if (items.length > 0 && substitutionChoices.length === 0) {
      setSubstitutionChoices(items.map(item => ({ originalProductId: item.product.id, selectedIds: [item.product.id] })));
    }
  }, [items, substitutionChoices]);

  const currentShoppingListItem = items[currentProductIndex];

  useEffect(() => {
    if (!currentShoppingListItem || !userLocation) return;

    const fetchSubstitutes = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (userLocation && userLocation.postcode && userLocation.radius) {
          params.append('postcode', userLocation.postcode);
          params.append('radius', userLocation.radius);
        }
        
        const response = await fetch(`/api/products/${currentShoppingListItem.product.id}/substitutes/?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSubstitutes(data);
        setSelectedOptions([currentShoppingListItem.product.id]); // Select original by default

        // If no substitutes found, automatically select original and advance
        if (data.length === 0) {
          setSubstitutionChoices(prevChoices => {
            const existingChoiceIndex = prevChoices.findIndex(choice => choice.originalProductId === currentShoppingListItem.product.id);
            if (existingChoiceIndex !== -1) {
              const updatedChoices = [...prevChoices];
              updatedChoices[existingChoiceIndex] = {
                ...updatedChoices[existingChoiceIndex],
                selectedIds: [currentShoppingListItem.product.id]
              };
              return updatedChoices;
            } else {
              return [...prevChoices, { originalProductId: currentShoppingListItem.product.id, selectedIds: [currentShoppingListItem.product.id] }];
            }
          });
          setCurrentProductIndex(prev => prev + 1);
        }

      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSubstitutes();
  }, [currentShoppingListItem, userLocation]); // Re-fetch when current product or user location changes

  const handleSelectOption = (productId) => {
    setSelectedOptions(prevSelected => {
      if (prevSelected.includes(productId)) {
        return prevSelected.filter(id => id !== productId);
      } else {
        return [...prevSelected, productId];
      }
    });
  };

  const handleNextProduct = () => {
    // Save current selections
    setSubstitutionChoices(prevChoices => {
      const existingChoiceIndex = prevChoices.findIndex(choice => choice.originalProductId === currentShoppingListItem.product.id);
      if (existingChoiceIndex !== -1) {
        const updatedChoices = [...prevChoices];
        updatedChoices[existingChoiceIndex] = {
          ...updatedChoices[existingChoiceIndex],
          selectedIds: selectedOptions
        };
        return updatedChoices;
      } else {
        return [...prevChoices, { originalProductId: currentShoppingListItem.product.id, selectedIds: selectedOptions }];
      }
    });
    setCurrentProductIndex(prev => prev + 1);
  };

  if (items.length === 0) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="info">Your shopping list is empty. Add some products to start splitting your cart!</Alert>
        <Button variant="primary" onClick={() => window.history.back()}>Go Back to Shopping</Button>
      </Container>
    );
  }

  if (!currentShoppingListItem) {
    return (
      <Container fluid className="mt-4">
        <h2>Substitution Complete!</h2>
        <p>You have reviewed all products in your cart.</p>
        {/* TODO: Display summary or navigate to next step */}
        <Button variant="primary">View Final Cart</Button>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <h2>Split My Cart: Product Substitution</h2>
      <p>Reviewing product {currentProductIndex + 1} of {items.length}</p>

      {loading && <Spinner animation="border" role="status"><span className="visually-hidden">Loading...</span></Spinner>}
      {error && <Alert variant="danger">Error: {error}</Alert>}

      <Row className="mt-4">
        <Col md={4}>
          <h4>Original Product</h4>
          <SelectableProductTile
            product={currentShoppingListItem.product}
            isSelected={selectedOptions.includes(currentShoppingListItem.product.id)}
            onSelect={handleSelectOption}
          />
        </Col>
        <Col md={8}>
          <h4>Substitutes</h4>
          <Row>
            {substitutes.length > 0 ? (
              substitutes.map(sub => (
                <Col key={sub.id} sm={6} md={4} lg={3} className="mb-4 p-2">
                  <SelectableProductTile
                    product={sub}
                    isSelected={selectedOptions.includes(sub.id)}
                    onSelect={handleSelectOption}
                  />
                </Col>
              ))
            ) : (
              <p>No substitutes found for this product.</p>
            )}
          </Row>
        </Col>
      </Row>

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

export default SubstitutionPage;
