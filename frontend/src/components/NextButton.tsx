'use client';

import { useRouter } from 'next/navigation';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import type { NextButtonPlacement, NextButtonProps } from '../types/NextButtonProps';

/**
 * Complete class strings, not fragments: Tailwind reads source as text and
 * generates nothing for a name it cannot find whole. See
 * `types/NextButtonProps.ts` for why the set is closed and what each value is.
 */
const PLACEMENT: Record<NextButtonPlacement, string> = {
  inline: '',
  floating: 'fixed bottom-8 right-8 z-50 h-16 w-16 rounded-full shadow-lg',
};

const NextButton = ({ onAfterNavigate, placement = 'inline' }: NextButtonProps) => {
  const router = useRouter();

  const handleNextClick = () => {
    router.push('/substitutions');

    if (onAfterNavigate) {
      onAfterNavigate();
    }
  };

  return (
    <Button
      onClick={handleNextClick}
      className={cn('bg-fill-success hover:bg-fill-success-hover', PLACEMENT[placement])}
    >
      Next
    </Button>
  );
};

export default NextButton;
