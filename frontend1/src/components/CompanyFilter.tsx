import React, { useState } from 'react';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

const companies = ['Coles', 'Woolworths', 'Aldi', 'IGA'];

interface CompanyFilterProps {
  onSelectionChange?: (selectedCompanies: string[]) => void;
}

const CompanyFilter: React.FC<CompanyFilterProps> = ({ onSelectionChange }) => {
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);

  const handleValueChange = (value: string[]) => {
    setSelectedCompanies(value);
    if (onSelectionChange) {
      onSelectionChange(value);
    }
  };

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium">Filter by Company</label>
      <ToggleGroup 
        type="multiple"
        variant="outline"
        value={selectedCompanies}
        onValueChange={handleValueChange}
        className="flex flex-wrap justify-start"
      >
        {companies.map(company => (
          <ToggleGroupItem key={company} value={company} aria-label={`Toggle ${company}`}>
            {company}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
};

export default CompanyFilter;
