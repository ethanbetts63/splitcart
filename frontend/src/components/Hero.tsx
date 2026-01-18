import React from 'react';
import confusedShopper from "../assets/confused_shopper.webp";
import confusedShopper320 from "../assets/confused_shopper-320w.webp";
import confusedShopper640 from "../assets/confused_shopper-640w.webp";
import confusedShopper768 from "../assets/confused_shopper-768w.webp";
import confusedShopper1024 from "../assets/confused_shopper-1024w.webp";
import confusedShopper1280 from "../assets/confused_shopper-1280w.webp";

interface HeroProps {
  title: React.ReactNode;
  subtitle: React.ReactNode;
  imageAlt: string;
  ctaElement?: React.ReactNode;
}

export const Hero: React.FC<HeroProps> = ({ title, subtitle, imageAlt, ctaElement }) => {
  const imageSrc = confusedShopper;
  const srcSet = `${confusedShopper320} 320w, ${confusedShopper640} 640w, ${confusedShopper768} 768w, ${confusedShopper1024} 1024w, ${confusedShopper1280} 1280w`;

  return (
    <section className="pt-4 pb-8 lg:py-0">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-12">
        <div className="px-4 lg:px-0">
          <img 
            width="1536"
            height="1024"
            src={imageSrc} 
            srcSet={srcSet}
            sizes="(min-width: 1024px) 50vw, 100vw"
            alt={imageAlt} 
            className="rounded-lg lg:rounded-none object-cover w-full h-full"
            fetchPriority="high"
          />
        </div>
        <div className="text-left text-black px-4 lg:px-8 flex flex-col justify-center lg:py-8">
          <h1 className="font-bold tracking-tight sm:text-5xl md:text-6xl">
            {title}
          </h1>
          <p className="mt-6 text-lg leading-8">
            {subtitle}
          </p>
          {ctaElement && (
            <div className="mt-6 flex justify-center">
              {ctaElement}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
