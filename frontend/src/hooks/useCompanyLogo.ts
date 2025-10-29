import { companyLogos } from '../lib/companies';
import { useImageAsset } from './useImageAsset';

export const useCompanyLogo = (companyName: string) => {
  const logoSrc = companyLogos[companyName];

  if (!logoSrc) {
    // Return a default state if the company name is invalid
    return { objectUrl: null, isLoading: false, error: new Error(`No logo found for company: ${companyName}`) };
  }

  return useImageAsset(logoSrc);
};