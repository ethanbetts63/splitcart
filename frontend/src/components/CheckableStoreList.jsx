
import React from 'react';
import { ListGroup, Form, Image } from 'react-bootstrap';

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
        <ListGroup>
            {stores.map(store => (
                <ListGroup.Item key={store.id} className="d-flex align-items-center">
                    <Form.Check 
                        type="checkbox"
                        id={`store-checkbox-${store.id}`}
                        checked={selectedStoreIds.has(store.id)}
                        onChange={() => onStoreSelect(store.id)}
                        className="me-3"
                    />
                    <Image src={companyLogos[store.company_name]} alt={`${store.company_name} logo`} height="20" className="me-2" />
                    <span>{store.store_name}</span>
                </ListGroup.Item>
            ))}
        </ListGroup>
    );
};

export default CheckableStoreList;
