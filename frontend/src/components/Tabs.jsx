import React from 'react';
import '../css/Tabs.css';

const Tabs = ({ results, baselineCost, activeTab, onTabClick }) => {
    return (
        <div className="tabs-container">
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
