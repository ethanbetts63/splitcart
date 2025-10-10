import React from 'react';
import '../css/ProductTile.css';

const SubstitutionInstructionsTile = () => {
  return (
    <div className="product-card">
      <div className="product-card-content" style={{ justifyContent: 'center' }}>
        <h3 style={{ textAlign: 'center', marginBottom: '1rem' }}>Why Substitution?</h3>
        <p>More options = more ways to save.</p>
        <p>Approving subs expands the AI's search space, letting it test far more combinations to find the lowest total price.</p>
        <p>Even a few subs can unlock major savings but the more the better. </p>
        <p>Don’t worry about price — just choose substitutes you’d accept. Adjust quantity if it takes more than one to replace the original.</p>
      </div>
    </div>
  );
};

export default SubstitutionInstructionsTile;
