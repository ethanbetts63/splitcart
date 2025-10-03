import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Container, Row, Col, Spinner, Alert } from 'react-bootstrap';
import OptimizationResultTile from '../components/OptimizationResultTile';

const FinalCartPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { cart, store_ids } = location.state || {};

    const [optimizationData, setOptimizationData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const splitCalledRef = useRef(false); // Flag to prevent double API calls

    useEffect(() => {
        if (!cart || !store_ids) {
            navigate('/');
            return;
        }

        if (splitCalledRef.current) {
            return; // Don't call API if it has already been called
        }
        splitCalledRef.current = true; // Set flag to true immediately

        const fetchOptimizedCart = async () => {
            try {
                const response = await axios.post('/api/cart/split/', {
                    cart: cart,
                    store_ids: store_ids,
                    max_stores_options: [2, 3, 4]
                });
                setOptimizationData(response.data);
            } catch (err) {
                setError(err.response ? err.response.data.error : 'An unexpected error occurred.');
            } finally {
                setLoading(false);
            }
        };

        fetchOptimizedCart();
    }, [cart, store_ids, navigate]);

    if (loading) {
        return (
            <Container className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
                <Spinner animation="border" variant="primary" />
            </Container>
        );
    }

    if (error) {
        return (
            <Container className="mt-5">
                <Alert variant="danger">Error: {error}</Alert>
            </Container>
        );
    }

    return (
        <div className="bg-light">
            <header className="bg-white text-dark p-4 text-center border-bottom">
                <h1>Optimized Shopping Cart</h1>
            </header>
            <Container className="py-4">
                {optimizationData && (
                    <Row>
                        {optimizationData.optimization_results.map((result, index) => (
                            <Col key={index} md={12} className="mb-4">
                                <OptimizationResultTile 
                                    result={result} 
                                    baselineCost={optimizationData.baseline_cost} 
                                />
                            </Col>
                        ))}
                    </Row>
                )}
            </Container>
        </div>
    );
};

export default FinalCartPage;