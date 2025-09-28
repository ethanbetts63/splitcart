import React, { useState } from 'react';
import { Card, Button, Form, InputGroup } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';

const ProductTile = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useShoppingList();

  const handleAdd = () => {
    addItem(product, quantity);
  };

  return (
    <Card style={{ width: '18rem' }}>
      <Card.Img variant="top" src={product.image_url || 'https://via.placeholder.com/150'} />
      <Card.Body>
        <Card.Title>{product.name}</Card.Title>
        <Card.Text as="div">
          {product.prices && product.prices.map(priceData => {
            const getCompanyColor = (companyName) => {
              switch (companyName.toLowerCase()) {
                case 'coles': return 'red';
                case 'woolworths': return 'green';
                case 'aldi': return 'blue';
                case 'iga': return 'orange';
                default: return 'black';
              }
            };
            const companyColor = getCompanyColor(priceData.company);
            const companyNameStyle = {
              color: companyColor,
              fontWeight: 'bold', // Make company name bold
            };
            const priceValueStyle = {
              color: priceData.is_lowest ? 'green' : 'black', // Price is green only if lowest, else black
              fontWeight: priceData.is_lowest ? 'bold' : 'normal',
            };
            return (
              <div key={priceData.company}>
                <span style={companyNameStyle}>{priceData.company}</span>: <span style={priceValueStyle}>${priceData.price_display}</span>
              </div>
            );
          })}
        </Card.Text>
        <div className="d-flex justify-content-between align-items-center mt-3">
          <InputGroup style={{ width: '120px' }}>
            <Button variant="outline-secondary" onClick={() => setQuantity(Math.max(1, quantity - 1))}>-</Button>
            <Form.Control value={quantity} readOnly className="text-center" />
            <Button variant="outline-secondary" onClick={() => setQuantity(quantity + 1)}>+</Button>
          </InputGroup>
          <Button variant="primary" onClick={handleAdd}>Add</Button>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ProductTile;
