import React from 'react';
import '../css/Tabs.css';

const Tabs = ({ results, baselineCost, activeTab, onTabClick, singleStoreResult }) => {
    return (
        <div className="tabs-container">
            {singleStoreResult && (
                <button
                    key="single"
                    className={`tab-item ${activeTab === 'single' ? 'active' : ''}`}
                    onClick={() => onTabClick('single')}
                >
                    <span className="tab-store-info">Best Single Store</span>
                    <span className="tab-price-info">
                        ${singleStoreResult.optimized_cost.toFixed(2)} ({singleStoreResult.items_found_count}/{singleStoreResult.total_items_in_cart} items)
                    </span>
                </button>
            )}
            {results.map((result, index) => {
                const savingsPercentage = baselineCost > 0 ? ((result.savings / baselineCost) * 100).toFixed(0) : 0;
                const isActive = activeTab === index;

                return (
                    <button
                        key={index}
                        className={`tab-item ${isActive ? 'active' : ''}`}
                        onClick={() => onTabClick(index)}
                    >
                        <span className="tab-store-info">{result.max_stores} Stores</span>
                        <span className="tab-price-info">
                            ${result.optimized_cost.toFixed(2)} (-{savingsPercentage}%)
                        </span>
                    </button>
                );
            })}
        </div>
    );
};

export default Tabs;
