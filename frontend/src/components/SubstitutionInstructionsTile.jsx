import React from 'react';
import '../css/ProductTile.css';

const SubstitutionInstructionsTile = () => {
  return (
    <div className="product-card">
      <div className="product-card-content" style={{ justifyContent: 'center', textAlign: 'center' }}>
        <p style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '1rem' }}>Why Substitution?</p>
        <p style={{ fontSize: '1.1rem', fontStyle: 'italic', marginBottom: '0.5rem' }}><strong>More options = more ways to save</strong></p>
        <p>Even a few subs can unlock major savings, but the <strong>more the better</strong>.</p>
        <p>Approving subs expands the AI's search space, letting it test more combinations to find the lowest total price.</p>
        <p><strong>Don’t worry about price</strong> — just choose substitutes you’d accept.</p>
        <p><strong>Adjust quantity</strong> if it takes more than one to replace the original.</p>
      </div>
    </div>
  );
};

export default SubstitutionInstructionsTile;