export interface HowItWorksStep {
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
