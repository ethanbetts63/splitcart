import splitcartLogo from "../assets/splitcart_symbol_v6.webp";
import splitcartLogo320 from "../assets/splitcart_symbol_v6-320w.webp";
import splitcartLogo640 from "../assets/splitcart_symbol_v6-640w.webp";
import splitcartLogo768 from "../assets/splitcart_symbol_v6-768w.webp";
import splitcartLogo1024 from "../assets/splitcart_symbol_v6-1024w.webp";
import splitcartLogo1280 from "../assets/splitcart_symbol_v6-1280w.webp";
import { assetSrc, assetSrcSet } from "@/lib/assets";
import { NavSearchBar } from "./NavSearchBar";
import { NavCartButton } from "./NavCartButton";
import { NavLocationButton } from "./NavLocationButton";
import { NavAuthButton } from "./NavAuthButton";

const NavBar = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white">

      {/* ── Main row ── */}
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8 gap-4">

        {/* Logo */}
        <a href="/" className="flex items-center space-x-2 flex-shrink-0">
          <img
            src={assetSrc(splitcartLogo)}
            srcSet={assetSrcSet([
              [splitcartLogo320, 320],
              [splitcartLogo640, 640],
              [splitcartLogo768, 768],
              [splitcartLogo1024, 1024],
              [splitcartLogo1280, 1280],
            ])}
            sizes="48px"
            alt="SplitCart Logo"
            className="h-12 w-12 sm:h-14 sm:w-14 flex-shrink-0"
          />
          <span className="font-bold text-2xl hidden md:block bg-yellow-300 px-0.5 py-1 rounded italic text-black">
            SplitCart
          </span>
        </a>

        {/* Search — desktop */}
        <div className="hidden sm:flex flex-1 items-center justify-center">
          <NavSearchBar className="max-w-md" />
        </div>

        {/* Icons */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <NavCartButton />
          <NavLocationButton />
          <NavAuthButton />
        </div>
      </div>

      {/* ── Search row — mobile ── */}
      <div className="sm:hidden px-4 pb-3">
        <NavSearchBar />
      </div>

    </header>
  );
};

export default NavBar;
