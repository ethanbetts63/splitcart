import React from 'react';
import '../css/SubstitutesToggle.css';

const SubstitutesToggle = ({ showSubstitutes, onToggle }) => {
    return (
        <div className="toggle-container">
            <span className={`toggle-label ${!showSubstitutes ? 'active' : ''}`}>
                Original Items
            </span>
            <label className="switch">
                <input 
                    type="checkbox" 
                    checked={showSubstitutes} 
                    onChange={onToggle} 
                />
                <span className="slider round"></span>
            </label>
            <span className={`toggle-label ${showSubstitutes ? 'active' : ''}`}>
                With Substitutes
            </span>
        </div>
    );
};

export default SubstitutesToggle;
