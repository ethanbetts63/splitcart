export interface MultiplePostcodeInputProps {
  value: string;
  onChange: (postcodes: string) => void;
  maxPostcodes?: number;
  className?: string;
}
