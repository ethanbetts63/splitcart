import SelectableProductTile from './SelectableProductTile';

const SubstitutesSection = ({ products, selectedOptions, onSelectOption, onQuantityChange, productQuantities = {} }) => {
  return (
    <div style={{ marginTop: '2rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(18rem, 1fr))', gap: '1rem' }}>
        {products.length > 0 ? (
          products.map(product => (
            <div key={product.id} style={{ position: 'relative', height: '100%' }}>
              <SelectableProductTile
                product={product}
                isSelected={selectedOptions.includes(product.id)}
                onSelect={onSelectOption}
                onQuantityChange={onQuantityChange}
                initialQuantity={productQuantities[product.id] || 1}
                is_original={product.is_original}
              />
              {product.is_original ? (
                <div 
                  style={{ position: 'absolute', top: 0, left: 0, backgroundColor: 'var(--primary)', color: 'white', padding: '0.25rem 0.5rem', fontSize: '0.75rem', borderTopLeftRadius: '0.25rem' }}
                >
                  Original Product
                </div>
              ) : product.level_description && (
                <div 
                  style={{ position: 'absolute', top: 0, left: 0, backgroundColor: 'var(--info)', color: 'white', padding: '0.25rem 0.5rem', fontSize: '0.75rem', borderTopLeftRadius: '0.25rem' }}
                >
                  {product.level_description}
                </div>
              )}
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
