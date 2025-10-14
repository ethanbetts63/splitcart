import React, { useState } from 'react';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

// Import logos
import aldiLogo from '@/assets/ALDI_logo.svg';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

// Update data structure to include logos
const companies = [
  { name: 'Coles', logo: colesLogo },
  { name: 'Woolworths', logo: woolworthsLogo },
  { name: 'Aldi', logo: aldiLogo },
  { name: 'IGA', logo: igaLogo },
];

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
        className="flex flex-wrap justify-start gap-2"
      >
        {companies.map(company => (
          <ToggleGroupItem key={company.name} value={company.name} aria-label={`Toggle ${company.name}`}>
            <img src={company.logo} alt={`${company.name} logo`} className="h-6 w-auto" />
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
};

export default CompanyFilter;