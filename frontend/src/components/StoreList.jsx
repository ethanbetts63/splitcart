
import React from 'react';
import { ListGroup, Form } from 'react-bootstrap';

const StoreList = ({ stores }) => {
    return (
        <ListGroup>
            {stores.map(store => (
                <ListGroup.Item key={store.id}>
                    <Form.Check 
                        type="checkbox"
                        id={`store-checkbox-${store.id}`}
                        label={`${store.store_name} (${store.company_name})`}
                        defaultChecked
                    />
                </ListGroup.Item>
            ))}
        </ListGroup>
    );
};

export default StoreList;
