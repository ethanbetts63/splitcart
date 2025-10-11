import React from 'react';
import DisplayOnlyProductTile from './DisplayOnlyProductTile';

// Logo imports
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

const StoreListComponent = ({ storeName, storeData, cart }) => {
    const style = {
        background: '#fff',
        padding: '1rem',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    };

    const { items, company_name } = storeData;
    const logo = companyLogos[company_name];

    const totalSpend = items.reduce((total, item) => total + item.price, 0);

    return (
        <div style={style}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                {logo && <img src={logo} alt={`${company_name} logo`} style={{ height: '30px', width: 'auto', maxWidth: '80px' }} />}
                <h6 style={{ fontWeight: 'bold', margin: 0, textAlign: 'center', flex: 1 }}>{storeName}</h6>
                <p style={{ fontWeight: 'bold', margin: 0, fontSize: '1.1rem' }}>${totalSpend.toFixed(2)}</p>
            </div>
            <div>
                {items.map((item, itemIndex) => {
                    const cartItem = cart.find(ci => ci.product && ci.product.name === item.product_name);
                    const displayItem = {
                        name: item.product_name,
                        brand: item.brand,
                        size: item.sizes.join(', '),
                        price: item.price,
                        quantity: cartItem ? cartItem.quantity : 1,
                        image_url: cartItem ? cartItem.product.image_url : ''
                    };

                    return <DisplayOnlyProductTile key={itemIndex} item={displayItem} />;
                })}
            </div>
        </div>
    );
};

export default StoreListComponent;
