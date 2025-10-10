import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import OptimizationResultTile from '../components/OptimizationResultTile';

const FinalCartPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { cart, store_ids, original_items } = location.state || {};

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
                    original_items: original_items,
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
    }, [cart, store_ids, original_items, navigate]);

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <div>Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ marginTop: '2rem' }}>
                <div style={{ color: 'red', border: '1px solid red', padding: '1rem' }}>Error: {error}</div>
            </div>
        );
    }

    return (
        <div style={{ background: 'var(--bg-light)' }}>
            <header style={{ background: 'var(--bg)', color: 'var(--text)', padding: '1rem', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>
                <h1>Optimized Shopping Cart</h1>
            </header>
            <div style={{ padding: '2rem' }}>
                {optimizationData && (
                    <div>
                        <h4 style={{ marginBottom: '1rem' }}>Savings with Substitutes:</h4>
                        {optimizationData.optimization_results.map((result, index) => (
                            <div key={index} style={{ marginBottom: '1.5rem' }}>
                                <OptimizationResultTile 
                                    result={result} 
                                    baselineCost={optimizationData.baseline_cost} 
                                />
                            </div>
                        ))}

                        {optimizationData.no_subs_results && (
                            <div style={{ marginTop: '3rem' }}>
                                <h4 style={{ marginBottom: '1rem' }}>Savings on Original Items Only:</h4>
                                {optimizationData.no_subs_results.optimization_results.map((result, index) => (
                                    <div key={index} style={{ marginBottom: '1.5rem' }}>
                                        <OptimizationResultTile 
                                            result={result} 
                                            baselineCost={optimizationData.no_subs_results.baseline_cost} 
                                        />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FinalCartPage;