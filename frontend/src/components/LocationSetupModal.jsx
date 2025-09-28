import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, InputGroup } from 'react-bootstrap';

const LocationSetupModal = ({ show, onHide, onSave }) => {
  const [postcode, setPostcode] = useState('');
  const [radius, setRadius] = useState(10); // Default radius in km

  const handleSave = () => {
    if (postcode && radius > 0) {
      onSave({ postcode, radius });
      onHide();
    }
  };

  return (
    <Modal show={show} onHide={onHide} backdrop="static" keyboard={false}>
      <Modal.Header>
        <Modal.Title>Set Your Location Preferences</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>To provide you with the most relevant product information, please tell us your preferred location and travel range.</p>
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Postcode</Form.Label>
            <Form.Control
              type="text"
              placeholder="e.g., 3000"
              value={postcode}
              onChange={(e) => setPostcode(e.target.value)}
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Travel Radius (km)</Form.Label>
            <InputGroup>
              <Button variant="outline-secondary" onClick={() => setRadius(Math.max(1, radius - 1))}>-</Button>
              <Form.Control
                type="number"
                value={radius}
                onChange={(e) => setRadius(parseInt(e.target.value) || 1)}
                min="1"
                className="text-center"
              />
              <Button variant="outline-secondary" onClick={() => setRadius(radius + 1)}>+</Button>
            </InputGroup>
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="primary" onClick={handleSave}>Save Location</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default LocationSetupModal;
