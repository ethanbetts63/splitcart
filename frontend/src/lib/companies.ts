import aldiLogo from '@/assets/ALDI_logo.webp';
import colesLogo from '@/assets/coles_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';
import { assetSrc } from './assets';

export const companyLogos: { [key: string]: string } = {
  'Aldi': assetSrc(aldiLogo),
  'Coles': assetSrc(colesLogo),
  'Woolworths': assetSrc(woolworthsLogo),
};

export const companyNames = Object.keys(companyLogos);
