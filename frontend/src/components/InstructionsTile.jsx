import React from 'react';
import '../css/InstructionsTile.css';

const InstructionsTile = () => {
  return (
    <div className="instructions-tile">
      <div className="instruction-item">
        <span className="instruction-number">1.</span>
        <div className="instruction-text">
          <span className="instruction-title">Pick your items:</span>
          <span className="instruction-subtext">Browse or search for products and add them to your cart.</span>
        </div>
      </div>
      <div className="instruction-item">
        <span className="instruction-number">2.</span>
        <div className="instruction-text">
          <span className="instruction-title">Pick substitutes:</span>
          <span className="instruction-subtext">For each item, you can select acceptable substitutes from other stores.</span>
        </div>
      </div>
      <div className="instruction-item">
        <span className="instruction-number">3.</span>
        <div className="instruction-text">
          <span className="instruction-title">Just hit split:</span>
          <span className="instruction-subtext">Our algorithm will find the cheapest combination of stores for your items and substitutes.</span>
        </div>
      </div>
    </div>
  );
};

export default InstructionsTile;
