import ProductCardContent from './ProductCardContent';

const ProductTile = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useShoppingList();

  const handleAdd = () => {
    addItem(product, quantity);
  };

  return (
    <Card style={{ width: '18rem' }}>
      <ProductCardContent product={product} />
      <Card.Body>
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
