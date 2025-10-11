import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Tabs from '../components/Tabs';
import TabPanel from '../components/TabPanel';

const FinalCartPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { cart, store_ids, original_items } = location.state || {};

    const [optimizationData, setOptimizationData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showSubstitutes, setShowSubstitutes] = useState(true);
    const [activeTab, setActiveTab] = useState(0);
    const splitCalledRef = useRef(false);

    useEffect(() => {
        if (!cart || !store_ids) {
            navigate('/');
            return;
        }

        if (splitCalledRef.current) {
            return;
        }
        splitCalledRef.current = true;

        const fetchOptimizedCart = async () => {
            try {
                const response = await axios.post('/api/cart/split/', {
                    cart: cart,
                    store_ids: store_ids,
                    original_items: original_items,
                    max_stores_options: [2, 3, 4]
                });
                setOptimizationData(response.data);
                if (response.data.best_single_store) {
                    setActiveTab('single');
                }

                // Default to no-subs view if subs view is empty
                if (!response.data.optimization_results || response.data.optimization_results.length === 0) {
                    setShowSubstitutes(false);
                }
            } catch (err) {
                setError(err.response ? err.response.data.error : 'An unexpected error occurred.');
            } finally {
                setLoading(false);
            }
        };

        fetchOptimizedCart();
    }, [cart, store_ids, original_items, navigate]);

    const handleToggle = () => {
        setShowSubstitutes(!showSubstitutes);
        setActiveTab(0); // Reset tab on toggle
    };

    const handleTabClick = (index) => {
        setActiveTab(index);
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <div>Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ marginTop: '2rem', padding: '0 2rem' }}>
                <div style={{ color: 'red', border: '1px solid red', padding: '1rem' }}>Error: {error}</div>
            </div>
        );
    }

    const subsResults = optimizationData?.optimization_results;
    const noSubsResults = optimizationData?.no_subs_results;

    const resultsToShow = showSubstitutes ? subsResults : noSubsResults?.optimization_results;
    const baselineToShow = showSubstitutes ? optimizationData?.baseline_cost : noSubsResults?.baseline_cost;
    const singleStoreResult = showSubstitutes ? optimizationData?.best_single_store : noSubsResults?.best_single_store;


    const canShowSubstitutes = subsResults && subsResults.length > 0;
    const canShowNoSubstitutes = noSubsResults && noSubsResults.optimization_results && noSubsResults.optimization_results.length > 0;

    return (
        <div style={{ background: 'var(--bg-light)', minHeight: '100vh', paddingTop: '2rem'}}>
            <div style={{ padding: '0 2rem' }}>
                <div style={{ background: 'var(--colorp3)', padding: '1rem', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
                    {resultsToShow && baselineToShow ? (
                        <>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                                <div style={{ flex: 1 }}>
                                    <Tabs
                                        results={resultsToShow}
                                        baselineCost={baselineToShow}
                                        activeTab={activeTab}
                                        onTabClick={handleTabClick}
                                        singleStoreResult={singleStoreResult}
                                    />
                                </div>
                                <h2 style={{ margin: 0, color: 'var(--colorp)', whiteSpace: 'nowrap', fontSize: '42px' }}>Optimized Cart</h2>
                                <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                                    {canShowSubstitutes && canShowNoSubstitutes && (
                                        <button onClick={handleToggle} style={{ background: 'red', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '20px', cursor: 'pointer', font: 'var(--font-numeric)', flexShrink: 0 }}>
                                            {showSubstitutes ? 'Disable Subs' : 'Enable Subs'}
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div>
                                {resultsToShow.map((result, index) => (
                                    <TabPanel
                                        key={index}
                                        result={result}
                                        baselineCost={baselineToShow}
                                        cart={original_items}
                                        isActive={activeTab === index}
                                    />
                                ))}

                                {singleStoreResult && activeTab === 'single' && (
                                    <div>
                                        <div style={{ padding: '1rem', background: 'var(--bg-light)', borderRadius: '8px', marginBottom: '1rem', textAlign: 'center' }}>
                                            <h5 style={{margin: 0}}>{singleStoreResult.items_found_count} out of {singleStoreResult.total_items_in_cart} items found at this store.</h5>
                                        </div>
                                        <TabPanel
                                            key="single"
                                            result={singleStoreResult}
                                            baselineCost={baselineToShow}
                                            cart={original_items}
                                            isActive={true}
                                        />
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div style={{ textAlign: 'center', marginTop: '1rem', padding: '1rem 0' }}>
                            <h4>
                                {showSubstitutes && !canShowSubstitutes
                                    ? "No optimization results available with substitutes."
                                    : "No optimization results available for the original items."}
                            </h4>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FinalCartPage;
