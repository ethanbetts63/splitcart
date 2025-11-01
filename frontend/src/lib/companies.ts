import aldiLogo from '@/assets/ALDI_logo.webp';
import colesLogo from '@/assets/coles_logo.webp';
import igaLogo from '@/assets/iga_logo.webp';
import woolworthsLogo from '@/assets/woolworths_logo.webp';

export const companyLogos: { [key: string]: string } = {
  'Aldi': aldiLogo,
  'Coles': colesLogo,
  'Iga': igaLogo,
  'Woolworths': woolworthsLogo,
};

export const companyNames = Object.keys(companyLogos);
