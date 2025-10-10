import SubstituteProductTile from './SubstituteProductTile';

const SubstitutesSection = ({ products, selectedOptions, onSelectOption, onQuantityChange, productQuantities = {} }) => {
  return (
    <div style={{ marginTop: '2rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(18rem, 1fr))', gap: '1rem' }}>
        {products.length > 0 ? (
          products.map(product => (
            <div key={product.id} style={{ position: 'relative', height: '100%' }}>
              <SubstituteProductTile
                product={product}
                isSelected={selectedOptions.includes(product.id)}
                onSelect={onSelectOption}
                onQuantityChange={onQuantityChange}
                initialQuantity={productQuantities[product.id] || 1}
                is_original={product.is_original}
              />
            </div>
          ))
        ) : (
          <p>No substitutes found for this product.</p>
        )}
      </div>
    </div>
  );
};

export default SubstitutesSection;
