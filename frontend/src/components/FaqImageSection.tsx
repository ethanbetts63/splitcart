import React from 'react';
import { FaqAccordion } from "./FaqAccordion";
import { Card, CardContent } from "@/components/ui/card";

interface FaqImageSectionProps {
  title: string;
  page: string;
  imageSrc: string;
  imageAlt: string;
}

export const FaqImageSection: React.FC<FaqImageSectionProps> = ({ title, page, imageSrc, imageAlt }) => {
  return (
    <Card className="overflow-hidden p-0 border-0 shadow-none">
      <CardContent className="grid p-0 md:grid-cols-2">
        <div className="p-6 md:p-8 order-2 md:order-1">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">{title}</h2>
          <FaqAccordion page={page} />
        </div>
        <div className="relative flex items-center justify-center h-full order-1 md:order-2">
          <img src={imageSrc} alt={imageAlt} className="h-full w-full object-contain dark:brightness-[0.2] dark:grayscale" />
        </div>
      </CardContent>
    </Card>
  );
};
