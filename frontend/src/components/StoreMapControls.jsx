import React from 'react';
import { Slider } from '@/components/ui/slider';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';

const StoreMapControls = ({ radius, setRadius, selectedCompanies, setSelectedCompanies, companyLogos }) => {
    return (
        <div style={{ backgroundColor: 'white', color: 'black', padding: '1rem', borderRadius: '8px', border: '0.3px solid var(--colorp2)', marginBottom: '1rem' }}>
            <label>Search Radius: {radius} km</label>
            <Slider
                defaultValue={[radius]}
                min={1}
                max={100}
                step={1}
                onValueChange={(value) => setRadius(value[0])}
                className="radius-slider"
                style={{ marginTop: '1rem' }}
            />
            <ToggleGroup
                type="multiple"
                variant="outline"
                value={selectedCompanies}
                onValueChange={setSelectedCompanies}
                style={{ marginTop: '1rem' }}
                className="company-toggle-group"
            >
                {Object.entries(companyLogos).map(([company, logo]) => (
                    <ToggleGroupItem key={company} value={company}>
                        <img src={logo} alt={company} style={{ height: '24px', width: 'auto' }} />
                    </ToggleGroupItem>
                ))}
            </ToggleGroup>
        </div>
    );
};

export default StoreMapControls;
