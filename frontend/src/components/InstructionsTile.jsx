import React from 'react';
import '../css/InstructionsTile.css';

const InstructionsTile = () => {
  return (
    <div className="instructions-tile">
      <div className="instruction-item">
        <span className="instruction-number">1.</span>
        <div className="instruction-text">
          <span className="instruction-title">Pick your items:</span>
          <span className="instruction-subtext">Browse or search for products. Add them to your cart. When you're done click "Next!" in the bottom right.</span>
        </div>
      </div>
      <div className="instruction-item">
        <span className="instruction-number">2.</span>
        <div className="instruction-text">
          <span className="instruction-title">Pick substitutes:</span>
          <span className="instruction-subtext"> We'll gather all the best options so you just have to click a couple boxes!</span>
        </div>
      </div>
      <div className="instruction-item">
        <span className="instruction-number">3.</span>
        <div className="instruction-text">
          <span className="instruction-title">The clever part:</span>
          <span className="instruction-subtext">The AI will split your cart across two or more stores to find the mathematically guaranteed lowest possible overall price.</span>
        </div>
      </div>
    </div>
  );
};

export default InstructionsTile;
