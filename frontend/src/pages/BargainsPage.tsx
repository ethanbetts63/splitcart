import { ProductCarousel } from '../components/ProductCarousel';
import { useStoreList } from '../context/StoreListContext';

const BargainsPage: React.FC = () => {
  const { selectedStoreIds } = useStoreList();

  const companies = [
    { id: 1, name: 'Coles' },
    { id: 2, name: 'Woolworths' },
    { id: 3, name: 'Aldi' },
    { id: 4, name: 'IGA' }
  ];

  const heroData = {
    title: 'Find the Best Bargains',
    introduction: 'Some supermarket prices aren’t just cheaper — they’re wildly cheaper. SplitCart scans Coles, Woolworths, Aldi, and IGA to find the biggest blowout bargains, showing you exactly where one store is undercutting the rest. No guessing, no scrolling — just the best deals, instantly.',
    imageUrl: '/images/bargains-hero.webp',
  };

  return (
    <div className="bg-gray-50 text-gray-800">
      {/* --- Hero Section --- */}
      <div className="relative h-96 bg-cover bg-center" style={{ backgroundImage: `url(${heroData.imageUrl})` }}>
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="text-center text-white p-8">
            <h1 className="text-5xl font-extrabold mb-4">{heroData.title}</h1>
            <p className="text-xl max-w-3xl mx-auto">{heroData.introduction}</p>
          </div>
        </div>
      </div>

      {/* --- Company Bargain Carousels --- */}
      <div className="py-12">
        <div className="container mx-auto px-4">
          {companies.map(company => (
            <div key={company.id} className="mb-12">
              <ProductCarousel
                title={`Bargains at ${company.name}`}
                sourceUrl="/api/bargains/carousel/"
                storeIds={selectedStoreIds}
                isDefaultStores={false}
                companyId={company.id}
                ordering="best_discount"
                onValidation={() => {}}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BargainsPage;