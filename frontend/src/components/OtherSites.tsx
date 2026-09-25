import { Card, CardContent, CardDescription, CardTitle } from '@/components/common/card';
import { Button } from '@/components/common/button';
import { ArrowRight } from 'lucide-react';
import type { OtherSitesProps } from '../types/OtherSitesProps';

const OtherSites = ({ sites }: OtherSitesProps) => {
  return (
    <div className="site-shell py-6">
      <h2 className="text-title font-bold text-center text-text-primary mb-8">
        Liked this site? Check out some of my others!
      </h2>
      <div className="flex justify-center">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {sites.map((site, index) => (
            <Card key={index} className="bg-surface-page border-0 shadow-md">
              <CardContent className="p-6 flex flex-col h-full">
                <div className="flex items-center mb-4">
                  <div className="flex-shrink-0 w-16 h-16 mr-4">
                    <img
                      src={site.logoSrc}
                      alt={`${site.name} Logo`}
                      className="w-full h-full object-contain"
                    />
                  </div>
                  <div className="flex-grow text-text-primary">
                    <CardTitle className="text-lead font-bold">{site.name}</CardTitle>
                  </div>
                </div>
                <CardDescription className="flex-grow mb-6 text-text-primary">
                  {site.description}
                </CardDescription>
                <div className="mt-auto flex justify-end">
                  <a href={site.url} target="_blank" rel="noopener noreferrer">
                    <Button className="bg-action-primary text-text-on-dark font-bold px-4 py-2 text-body hover:bg-action-primary-hover flex items-center gap-2">
                      Visit Site <ArrowRight className="h-4 w-4" />
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OtherSites;
