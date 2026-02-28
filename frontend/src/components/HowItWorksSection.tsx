interface HowItWorksStep {
  step: number;
  title: string;
  description: string;
  image: {
    src: string;
    srcSet: string;
    sizes: string;
    alt: string;
  };
}

interface HowItWorksSectionProps {
  steps: HowItWorksStep[];
}

export const HowItWorksSection = ({ steps }: HowItWorksSectionProps) => {
  return (
    <div className="bg-[#f5f0eb] py-5">
      <div className="container mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            How It Works
          </h2>
        </div>

        <div className="flex gap-6 lg:gap-8 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide max-w-5xl mx-auto">
          {steps.map((step) => (
            <div
              key={step.step}
              className="bg-white rounded-2xl shadow-md overflow-hidden flex-shrink-0 w-80 md:w-auto md:flex-1 snap-start"
            >
              <div className="relative">
                <img
                  src={step.image.src}
                  srcSet={step.image.srcSet}
                  sizes={step.image.sizes}
                  alt={step.image.alt}
                  className="w-full h-52 md:h-56 lg:h-64 object-cover"
                  loading="lazy"
                />
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 flex items-center justify-center w-11 h-11 bg-yellow-300 text-black text-lg font-bold rounded-md shadow-lg">
                  {step.step}
                </span>
              </div>

              <div className="pt-9 pb-7 px-6 text-center">
                <h3 className="text-xl md:text-2xl font-bold text-gray-900">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm md:text-base text-gray-600 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
