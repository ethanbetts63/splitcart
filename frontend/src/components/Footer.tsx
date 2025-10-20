import { Link } from 'react-router-dom';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-100 dark:bg-gray-800 mt-auto">
      <div className="container mx-auto px-6 py-8">
        <div className="flex flex-col items-center sm:flex-row sm:justify-between">
          <p className="text-sm text-gray-500 dark:text-gray-400">© {currentYear} SplitCart. All Rights Reserved.</p>
          <div className="flex mt-4 sm:m-0">
            <Link to="/about" className="px-4 text-sm text-gray-700 hover:underline dark:text-gray-200">About</Link>
            <Link to="/privacy" className="px-4 text-sm text-gray-700 hover:underline dark:text-gray-200">Privacy Policy</Link>
            <Link to="/contact" className="px-4 text-sm text-gray-700 hover:underline dark:text-gray-200">Contact</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
