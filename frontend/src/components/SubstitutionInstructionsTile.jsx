import React from 'react';
import '../css/ProductTile.css';

const SubstitutionInstructionsTile = () => {
  return (
    <div className="product-card">
      <div className="product-card-content" style={{ justifyContent: 'center' }}>
        <h3 style={{ textAlign: 'center', marginBottom: '1rem' }}>Why Substitution?</h3>
        <p>More options = more ways to save.</p>
        <p>Each item locks the AI to stores that stock that exact product.</p>
        <p>Adding substitutes — similar brands or sizes — expands its search space, letting it test far more combinations to find the lowest total price.</p>
        <p>Even a few substitutes can unlock major savings but the more the better. </p>
      </div>
    </div>
  );
};

export default SubstitutionInstructionsTile;
