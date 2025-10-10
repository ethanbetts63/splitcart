import SubstituteProductTile from './SubstituteProductTile';
import subImage from '../assets/sub_image.png';

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
        <div style={{ width: '18rem', margin: 'auto' }}>
          <img src={subImage} alt="Substitution suggestion" style={{ width: '100%', borderRadius: '8px' }} />
        </div>
      </div>
    </div>
  );
};

export default SubstitutesSection;
