import React from 'react';
import StoreMap from '@/components/StoreMap';
import RadiusSlider from '@/components/RadiusSlider';

const EditLocationPage = () => {
  return (
    <div className="flex h-full w-full">
      {/* Left Column for Controls and List */}
      <div className="w-1/3 border-r p-4 flex flex-col gap-4">
        <div className="grid gap-4">
          <h3 className="text-lg font-semibold">Controls</h3>
          <RadiusSlider />
          {/* Company Toggles will go here */}
        </div>
        <div>
          <h3 className="text-lg font-semibold">Nearby Stores</h3>
          <p className="text-sm text-muted-foreground">Checkable store list will go here.</p>
        </div>
      </div>

      {/* Right Column for the Map */}
      <div className="flex-grow">
        <StoreMap />
      </div>
    </div>
  );
};

export default EditLocationPage;
