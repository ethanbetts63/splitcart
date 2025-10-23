import React, { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface MultiplePostcodeInputProps {
  value: string; // Comma-separated string of postcodes
  onChange: (postcodes: string) => void;
  maxPostcodes?: number;
  className?: string;
}

const MultiplePostcodeInput: React.FC<MultiplePostcodeInputProps> = ({
  value,
  onChange,
  maxPostcodes = 5,
  className,
}) => {
  const [postcodes, setPostcodes] = useState<string[]>(value ? value.split(',').filter(p => p.length === 4) : []);
  const [inputValue, setInputValue] = useState<string>("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync internal state with external value prop
  useEffect(() => {
    const newPostcodes = value ? value.split(',').filter(p => p.length === 4) : [];
    // Only update if the external value has truly changed to avoid infinite loops
    if (JSON.stringify(newPostcodes) !== JSON.stringify(postcodes)) {
      setPostcodes(newPostcodes);
    }
  }, [value]);

  // Notify parent of changes
  useEffect(() => {
    onChange(postcodes.join(','));
  }, [postcodes, onChange]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    // Only allow digits
    if (!/^[0-9]*$/.test(newValue)) {
      return;
    }

    setInputValue(newValue);

    // Automatic badging after 4 digits
    if (newValue.length === 4 && postcodes.length < maxPostcodes) {
      setPostcodes(prev => {
        // Prevent duplicates
        if (!prev.includes(newValue)) {
          return [...prev, newValue];
        }
        return prev;
      });
      setInputValue(""); // Clear input after badging
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Backspace to de-badgify or delete last digit
    if (e.key === 'Backspace' && inputValue === '' && postcodes.length > 0) {
      e.preventDefault(); // Prevent default browser backspace behavior
      setPostcodes(prev => {
        const lastPostcode = prev[prev.length - 1];
        setInputValue(lastPostcode.slice(0, -1)); // Put it back into the input, but with the last char removed
        return prev.slice(0, -1); // Remove from badges
      });
    }
    // Prevent typing if max postcodes reached and input is empty
    if (postcodes.length >= maxPostcodes && inputValue === '' && e.key !== 'Backspace') {
      e.preventDefault();
    }
  };

  const handleRemovePostcode = (postcodeToRemove: string) => {
    setPostcodes(prev => prev.filter(p => p !== postcodeToRemove));
  };

  const isMaxReached = postcodes.length >= maxPostcodes;

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex flex-wrap items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm has-[:focus-visible]:ring-1 has-[:focus-visible]:ring-ring">
        {postcodes.map(postcode => (
          <Badge 
            key={postcode} 
            variant="secondary" 
            className="flex items-center gap-1 pr-1"
            onClick={() => handleRemovePostcode(postcode)} // Allow clicking badge to remove
          >
            {postcode}
            <span className="cursor-pointer text-xs font-bold">x</span>
          </Badge>
        ))}
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          maxLength={4} // Max 4 digits for a postcode
          className="flex-grow border-none bg-transparent shadow-none focus-visible:ring-0 focus-visible:outline-none p-0 h-auto"
          placeholder={postcodes.length === 0 ? "Enter postcodes (max 5)" : ""}
          disabled={isMaxReached && inputValue === ''}
        />
      </div>
      <p className="text-sm text-muted-foreground">
        Enter up to the postcode for any area you might shop in. e.g. Home, Work, School.
      </p>
    </div>
  );
};

export default MultiplePostcodeInput;
