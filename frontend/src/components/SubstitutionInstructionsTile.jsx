import React from 'react';
import '../css/ProductTile.css';

const SubstitutionInstructionsTile = () => {
  return (
    <div className="product-card">
      <div className="product-card-content" style={{ justifyContent: 'center' }}>
        <h3 style={{ textAlign: 'center', marginBottom: '1rem' }}>How Substitution Works</h3>
        <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
          <li style={{ marginBottom: '0.5rem' }}>Review the original product and the available substitutes.</li>
          <li style={{ marginBottom: '0.5rem' }}>Click 'Approve' to add a substitute to your potential shopping list.</li>
          <li style={{ marginBottom: '0.5rem' }}>You can approve multiple substitutes.</li>
          <li style={{ marginBottom: '0.5rem' }}>Click 'Remove' to take a substitute off the list.</li>
          <li style={{ marginBottom: '0.5rem' }}>Adjust the quantity for each item as needed.</li>
          <li style={{ marginBottom: '0.5rem' }}>When you're done, click 'Next Product' or 'Split My Cart'.</li>
        </ul>
      </div>
    </div>
  );
};

export default SubstitutionInstructionsTile;
