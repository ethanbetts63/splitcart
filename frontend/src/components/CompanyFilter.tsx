import React, { useState } from 'react';
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { companyNames } from '@/lib/companies';
import { useCompanyLogo } from '@/hooks/useCompanyLogo';
import { Skeleton } from '@/components/ui/skeleton';

interface CompanyFilterProps {
  onSelectionChange?: (selectedCompanies: string[]) => void;
}

// Internal component to handle the logo loading state
const CompanyLogo = ({ companyName }: { companyName: string }) => {
  const { objectUrl, isLoading, error } = useCompanyLogo(companyName);

  if (isLoading) {
    return <Skeleton className="h-6 w-12" />;
  }

  if (error || !objectUrl) {
    return <div className="h-6 w-12 flex items-center justify-center text-xs text-red-500">?</div>;
  }

  return <img src={objectUrl} alt={`${companyName} logo`} className="h-6 w-auto" />;
};

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
        {companyNames.map(name => (
          <ToggleGroupItem 
            key={name} 
            value={name} 
            aria-label={`Toggle ${name}`}
            className="data-[state=on]:bg-white data-[state=on]:text-black data-[state=off]:bg-destructive data-[state=off]:text-destructive-foreground"
          >
            <CompanyLogo companyName={name} />
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
};

export default CompanyFilter;