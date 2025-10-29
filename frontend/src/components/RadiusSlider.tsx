import React, { useState } from 'react';
import { Slider } from './ui/slider';

interface RadiusSliderProps {
  defaultValue?: number;
  min?: number;
  max?: number;
  step?: number;
  onValueChange?: (value: number) => void;
}

const RadiusSlider: React.FC<RadiusSliderProps> = ({ 
  defaultValue = 5, 
  min = 1, 
  max = 30, 
  step = 1, 
  onValueChange 
}) => {
  const [radius, setRadius] = useState(defaultValue);

  const handleValueChange = (value: number[]) => {
    const newRadius = value[0];
    setRadius(newRadius);
    if (onValueChange) {
      onValueChange(newRadius);
    }
  };

  return (
    <div className="grid gap-2">
      <div className="flex items-center justify-between">
        <label htmlFor="radius-slider" className="text-sm font-medium">Radius</label>
        <span className="text-sm text-muted-foreground">{radius} km</span>
      </div>
      <Slider
        id="radius-slider"
        defaultValue={[radius]}
        min={min}
        max={max}
        step={step}
        onValueChange={handleValueChange}
        className="w-full"
      />
    </div>
  );
};

export default RadiusSlider;
