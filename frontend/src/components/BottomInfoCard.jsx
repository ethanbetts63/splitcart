import React from 'react';
import '../css/BottomInfoCard.css';

const BottomInfoCard = () => {
  return (
    <div className="bottom-info-card">
      <div className="info-item">
        <div className="info-text">
          <span className="info-title">Did you know?</span>
          <span className="info-subtext">The average Austrlian household spends $200 (exc. alcohol) on groceries per week. Our algorithm can save you 10% on average which means 20 bucks! That's almost two Melbourne coffees or a netflix subscription! You're welcome! </span>
        </div>
      </div>
    </div>
  );
};

export default BottomInfoCard;
