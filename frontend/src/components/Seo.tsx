import React from 'react';
import { Helmet } from 'react-helmet-async';

interface SeoProps {
  title: string;
  description?: string;
  canonicalPath?: string;
  ogType?: 'website' | 'article';
  ogImage?: string;
  noindex?: boolean;
  structuredData?: object;
}

const Seo: React.FC<SeoProps> = ({ title, description, canonicalPath, ogType = 'website', ogImage, noindex, structuredData }) => {
  const siteUrl = 'https://www.splitcart.com.au';
  const canonicalUrl = canonicalPath ? `${siteUrl}${canonicalPath}` : undefined;
  const imageUrl = ogImage ? `${siteUrl}${ogImage}` : `${siteUrl}/static/square-image.jpg`; // Fallback image

  return (
    <Helmet>
      {/* Standard SEO */}
      <title>{title}</title>
      {description && <meta name="description" content={description} />}
      {noindex && <meta name="robots" content="noindex" />}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}
      
      {/* Open Graph Tags (Facebook, etc.) */}
      <meta property="og:title" content={title} />
      {description && <meta property="og:description" content={description} />}
      <meta property="og:type" content={ogType} />
      {canonicalUrl && <meta property="og:url" content={canonicalUrl} />}
      <meta property="og:image" content={imageUrl} />
      
      {/* Twitter Card Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      {description && <meta name="twitter:description" content={description} />}
      <meta name="twitter:image" content={imageUrl} />

      {/* Render structured data if provided */}
      {structuredData && (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      )}
    </Helmet>
  );
};

export default Seo;
