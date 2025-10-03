
import React from 'react';
import { ListGroup, Form } from 'react-bootstrap';

const CheckableStoreList = ({ stores, selectedStoreIds, onStoreSelect }) => {
    return (
        <ListGroup>
            {stores.map(store => (
                <ListGroup.Item key={store.id}>
                    <Form.Check 
                        type="checkbox"
                        id={`store-checkbox-${store.id}`}
                        label={`${store.store_name} (${store.company_name})`}
                        checked={selectedStoreIds.has(store.id)}
                        onChange={() => onStoreSelect(store.id)}
                    />
                </ListGroup.Item>
            ))}
        </ListGroup>
    );
};

export default CheckableStoreList;
