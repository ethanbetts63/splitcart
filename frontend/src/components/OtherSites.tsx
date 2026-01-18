import React from 'react';
import { Card, CardContent, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

interface OtherSite {
    name: string;
    logoSrc: string;
    description: string;
    url: string;
}

interface OtherSitesProps {
    sites: OtherSite[];
}

const OtherSites: React.FC<OtherSitesProps> = ({ sites }) => {
    return (
        <div className="container mx-auto py-6">
            <h2 className="text-3xl font-bold text-center text-black mb-8">
                Liked this site? Check out some of my others!
            </h2>
            <div className="flex justify-center">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
                    {sites.map((site, index) => (
                        <Card key={index} className="bg-white border-0 shadow-md">
                            <CardContent className="p-6 flex flex-col h-full">
                                <div className="flex items-center mb-4">
                                    <div className="flex-shrink-0 w-16 h-16 mr-4">
                                        <img src={site.logoSrc} alt={`${site.name} Logo`} className="w-full h-full object-contain" />
                                    </div>
                                    <div className="flex-grow text-black">
                                        <CardTitle className="text-xl font-bold">{site.name}</CardTitle>
                                    </div>
                                </div>
                                <CardDescription className="flex-grow mb-6 text-black">{site.description}</CardDescription>
                                <div className="mt-auto flex justify-end">
                                    <a href={site.url} target="_blank" rel="noopener noreferrer">
                                        <Button className="bg-primary text-black font-bold px-4 py-2 text-sm hover:bg-primary/90 flex items-center gap-2">
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
