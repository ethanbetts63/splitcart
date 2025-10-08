import React from 'react';

// Logos
import aldiLogo from '../assets/ALDI_logo.svg';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';

const companyLogos = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

const PriceDisplay = ({ prices }) => {
  const pricesToShow = prices || [];

  const getFontSize = (numPrices) => {
    if (numPrices === 1) return '1.5rem';
    if (numPrices === 2) return '1.2rem';
    return '1rem';
  };

  const containerStyle = {
    backgroundColor: 'white',
    padding: '0.5rem',
    borderRadius: '8px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
    gap: '0.5rem',
    marginTop: '0.5rem',
    flex: 1,
    marginRight: '0.5rem',
  };

  const priceItemStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const fontSize = getFontSize(pricesToShow.length);

  return (
    <div style={containerStyle}>
      {pricesToShow.map(priceData => (
        <div key={priceData.company} style={priceItemStyle}>
          <img src={companyLogos[priceData.company]} alt={`${priceData.company} logo`} style={{ height: '20px', marginRight: '0.25rem' }} />
          <span style={{ color: priceData.is_lowest ? 'var(--success)' : 'var(--text)', fontSize: fontSize }}>
            ${priceData.price_display}
          </span>
        </div>
      ))}
    </div>
  );
};

export default PriceDisplay;
