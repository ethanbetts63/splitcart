import type { SeoProps } from '../types/SeoProps';

const Seo: React.FC<SeoProps> = ({ title, description, canonicalPath, ogType = 'website', ogImage, noindex, structuredData }) => {
  void title;
  void description;
  void canonicalPath;
  void ogType;
  void ogImage;
  void noindex;

  return (
    <>
      {structuredData && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      )}
    </>
  );
};

export default Seo;
