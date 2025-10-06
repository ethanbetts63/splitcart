
import React from 'react';

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

const CheckableStoreList = ({ stores, selectedStoreIds, onStoreSelect }) => {
    return (
        <div>
            {stores.map(store => (
                <div key={store.id} onClick={() => onStoreSelect(store.id)} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                    <input 
                        type="checkbox"
                        id={`store-checkbox-${store.id}`}
                        checked={selectedStoreIds.has(store.id)}
                        onChange={() => {}} // The onClick on the div handles the logic
                        style={{ marginRight: '1rem' }}
                    />
                    <img src={companyLogos[store.company_name]} alt={`${store.company_name} logo`} height="20" style={{ marginRight: '0.5rem' }} />
                    <span>{store.store_name}</span>
                </div>
            ))}
        </div>
    );
};

export default CheckableStoreList;
