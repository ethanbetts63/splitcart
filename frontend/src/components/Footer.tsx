import Image from 'next/image';
import Link from 'next/link';

import freeTheDeskLogo from '@/assets/freethedesk_logo_512x512.png';

/* eslint-disable no-restricted-syntax -- third-party brand colours */
const FTD_BLUE = 'text-[#1a5fa8]';
const FTD_DEEP_BLUE = 'text-[#0b64d6]';
/* eslint-enable no-restricted-syntax */

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-surface-sunken mt-auto">
      <div className="site-shell px-6 py-section">
        <div className="flex flex-col items-center sm:flex-row sm:justify-between">
          <p className="text-body text-text-primary">
            © {currentYear} SplitCart. All Rights Reserved.
          </p>
          <div className="flex mt-4 sm:m-0">
            <Link href="/privacy" className="px-4 text-body text-text-primary hover:underline">
              Privacy Policy
            </Link>
            <Link href="/contact" className="px-4 text-body text-text-primary hover:underline">
              Contact
            </Link>
          </div>
          <a
            href="https://www.freethedesk.com.au/"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex items-center gap-3xs text-body text-text-primary transition-opacity hover:opacity-70 sm:m-0"
          >
            <span>Website by</span>
            <Image
              src={freeTheDeskLogo}
              alt=""
              width={22}
              height={22}
              className="h-[22px] w-[22px]"
            />
            {/* One text node, so a crawler reads one word. Split into coloured spans,
               Google read the anchor as "free the desk". The coloured wordmark is drawn
               from CSS content, which is not text, and is hidden from screen readers. */}
            <span className="sr-only">freethedesk</span>
            <span
              aria-hidden="true"
              className="font-black leading-none tracking-[-0.085em] text-text-primary"
            >
              <span className="before:content-['free']" />
              <span className={`${FTD_BLUE} before:content-['the']`} />
              <span className="before:content-['desk']" />
              <span className={`${FTD_DEEP_BLUE} before:content-['.']`} />
            </span>
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
