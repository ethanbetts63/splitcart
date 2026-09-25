import Link from 'next/link';

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
        </div>
      </div>
    </footer>
  );
};

export default Footer;
