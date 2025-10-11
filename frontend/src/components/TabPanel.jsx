import React from 'react';
import OptimizationResultTile from './OptimizationResultTile';

const TabPanel = ({ result, baselineCost, cart, isActive }) => {
    if (!isActive) {
        return null;
    }

    return (
        <div className="tab-panel">
            <OptimizationResultTile 
                result={result} 
                baselineCost={baselineCost} 
                cart={cart}
            />
        </div>
    );
};

export default TabPanel;
