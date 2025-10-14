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

const PriceDisplay = ({ prices, showBackground = true, variant = 'trolley', onPriceSelect, selectedPrice }) => {
  const pricesToShow = prices || [];

  const getFontSize = (numPrices) => {
    if (variant === 'product-tile') {
      if (numPrices === 1) return '1.2rem';
      if (numPrices === 2) return '1rem';
      return '0.9rem';
    }
    // trolley styles (original)
    if (numPrices === 1) return '1.5rem';
    if (numPrices === 2) return '1.1rem';
    return '1rem';
  };

  const baseContainerStyle = {
    backgroundColor: showBackground ? 'white' : 'transparent',
    borderRadius: '8px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
  };

  const variantStyles = {
    trolley: {
      padding: '0.5rem',
      marginTop: '0.5rem',
      flex: 1,
      marginRight: '0.5rem',
      gap: '0.25rem',
    },
    'product-tile': {
      padding: '0.1rem',
      marginTop: '0.25rem',
      gap: '0.1rem',
    },
  };

  const containerStyle = { ...baseContainerStyle, ...variantStyles[variant] };

  if (pricesToShow.length === 1) {
    containerStyle.gridTemplateColumns = '1fr';
    containerStyle.justifyItems = 'center';
  } else if (pricesToShow.length >= 2) {
    containerStyle.gridTemplateColumns = 'repeat(2, 1fr)';
  }

  const priceItemStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const fontSize = getFontSize(pricesToShow.length);

  const imageSize = variant === 'product-tile' ? '25px' : '20px';

  const imageStyle = {
    width: imageSize,
    height: imageSize,
    objectFit: 'contain',
    marginRight: '0.25rem',
  };

  return (
    <div style={containerStyle}>
      {pricesToShow.map(priceData => {
        const isSelected = selectedPrice && selectedPrice.company === priceData.company;
        const itemStyle = {
          ...priceItemStyle,
          cursor: onPriceSelect ? 'pointer' : 'default',
          border: isSelected ? '2px solid var(--colorp)' : '2px solid transparent',
          borderRadius: '8px',
          padding: '0.2rem',
          backgroundColor: isSelected ? 'var(--colorp4)' : 'transparent',
        };

        return (
          <div key={priceData.company} style={itemStyle} onClick={() => onPriceSelect && onPriceSelect(priceData)}>
            <img src={companyLogos[priceData.company]} alt={`${priceData.company} logo`} style={imageStyle} />
            <span style={{ color: priceData.is_lowest ? 'var(--success)' : 'var(--text)', fontSize: fontSize, fontFamily: 'var(--font-numeric)', whiteSpace: 'nowrap' }}>
              ${priceData.price_display}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default PriceDisplay;
