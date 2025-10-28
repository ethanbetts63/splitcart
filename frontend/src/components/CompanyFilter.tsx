import React from 'react';
import { Checkbox } from "@/components/ui/checkbox";
import { companyNames } from '@/lib/companies';
import { useCompanyLogo } from '@/hooks/useCompanyLogo';
import { Skeleton } from '@/components/ui/skeleton';

interface CompanyFilterProps {
  selectedCompanies?: string[];
  onSelectionChange: (selectedCompanies: string[]) => void;
}

// Internal component to handle the logo loading state
const CompanyLogo = ({ companyName }: { companyName: string }) => {
  const { objectUrl, isLoading, error } = useCompanyLogo(companyName);

  if (isLoading) {
    return <Skeleton className="h-3 w-5" />;
  }

  if (error || !objectUrl) {
    return <div className="h-3 w-5 flex items-center justify-center text-xs text-red-500">?</div>;
  }

  return <img src={objectUrl} alt={`${companyName} logo`} className="h-5 w-5" />;
};

const CompanyFilter: React.FC<CompanyFilterProps> = ({ selectedCompanies = [], onSelectionChange }) => {

  const handleCheckboxChange = (companyName: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedCompanies, companyName]);
    } else {
      onSelectionChange(selectedCompanies.filter(name => name !== companyName));
    }
  };

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium">Filter by Company</label>
      <div className="flex flex-wrap justify-start gap-2">
        {companyNames.map(name => (
          <div 
            key={name} 
            className="flex items-center space-x-2 rounded-md border p-2 cursor-pointer"
            onClick={() => handleCheckboxChange(name, !selectedCompanies.includes(name))}
          >
            <Checkbox
              id={name}
              checked={selectedCompanies.includes(name)}
              onCheckedChange={(checked: boolean) => handleCheckboxChange(name, checked)}
            />
            <div
              className="flex items-center gap-2 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              <CompanyLogo companyName={name} />
              <span className="hidden md:inline">{name}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CompanyFilter;