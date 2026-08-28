import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  useLocation,
} from "react-router-dom";
import {
  Menu,
  Moon,
  Sun,
  X,
} from "lucide-react";

import logo from "../../assets/branding/sauti-yo-logo-horizontal.png";
import logoLight from "../../assets/branding/sauti-yo-logo-light.png";

const navigation = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  { to: "/rights", label: "Know Your Rights" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/access", label: "Access" },
  { to: "/community", label: "Community Voice" },
  { to: "/support", label: "Find Support" },
];

export default function Header() {
  const location = useLocation();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem("sauti-yo-theme");

    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;

    const useDark =
      savedTheme === "dark" ||
      (!savedTheme && prefersDark);

    setDarkMode(useDark);

    document.documentElement.classList.toggle(
      "dark",
      useDark,
    );
  }, []);

  useEffect(() => {
    setMobileOpen(false);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }, [location.pathname]);

  const toggleTheme = () => {
    const nextMode = !darkMode;

    setDarkMode(nextMode);

    document.documentElement.classList.toggle(
      "dark",
      nextMode,
    );

    localStorage.setItem(
      "sauti-yo-theme",
      nextMode ? "dark" : "light",
    );
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/95 shadow-[0_4px_20px_rgba(0,0,0,0.04)] backdrop-blur-md">
      <div className="site-container flex min-h-[82px] items-center justify-between gap-3 xl:min-h-[86px] xl:gap-4">
        {/* Sauti Yo brand */}
        <Link
          to="/"
          aria-label="Sauti Yo — Know. Act. Be Heard. — home"
          className="group flex min-w-0 shrink-0 flex-col items-start justify-center"
        >
          <img
            src={darkMode ? logoLight : logo}
            alt="Sauti Yo"
            className="block h-auto w-[150px] object-contain object-left sm:w-[165px] lg:w-[160px] xl:w-[178px]"
          />

          <span className="mt-0.5 pl-1 text-[9px] font-bold uppercase leading-none tracking-[0.22em] text-gold-deep transition-colors group-hover:text-gold dark:text-gold sm:text-[10px]">
            Know. Act. Be Heard.
          </span>
        </Link>

        {/* Desktop navigation */}
        <nav
          aria-label="Main navigation"
          className="hidden flex-1 items-center justify-center gap-4 lg:flex xl:gap-6"
        >
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `group relative whitespace-nowrap py-2 text-[13px] font-medium transition-all duration-300 xl:text-sm ${
                  isActive
                    ? "text-gold-deep dark:text-gold"
                    : "text-text-secondary hover:text-gold"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`block transition-transform duration-300 ${
                      isActive ? "-translate-y-0.5" : ""
                    }`}
                  >
                    {item.label}
                  </span>

                  <span
                    className={`absolute bottom-0 left-0 h-[2px] bg-gold transition-all duration-300 ${
                      isActive
                        ? "w-full"
                        : "w-0 group-hover:w-full"
                    }`}
                  />
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Desktop actions */}
        <div className="hidden shrink-0 items-center gap-2 lg:flex">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={
              darkMode
                ? "Switch to light mode"
                : "Switch to dark mode"
            }
            title={
              darkMode
                ? "Switch to light mode"
                : "Switch to dark mode"
            }
            className="flex h-11 w-11 items-center justify-center rounded-md border border-border bg-surface text-text-primary transition-all duration-200 hover:border-gold hover:bg-gold/10 hover:text-gold focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/25"
          >
            {darkMode ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>

          <NavLink
            to="/rights"
            className="btn-primary ml-1 whitespace-nowrap"
          >
            Start Here
          </NavLink>
        </div>

        {/* Mobile actions */}
        <div className="flex shrink-0 items-center gap-2 lg:hidden">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={
              darkMode
                ? "Switch to light mode"
                : "Switch to dark mode"
            }
            className="flex h-11 w-11 items-center justify-center rounded-md border border-border bg-surface text-text-primary transition-all duration-200 hover:border-gold hover:bg-gold/10 hover:text-gold focus:outline-none focus:ring-2 focus:ring-gold/25"
          >
            {darkMode ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>

          <button
            type="button"
            onClick={() =>
              setMobileOpen((current) => !current)
            }
            aria-expanded={mobileOpen}
            aria-label={
              mobileOpen
                ? "Close navigation menu"
                : "Open navigation menu"
            }
            className="flex h-11 w-11 items-center justify-center rounded-md border border-border bg-surface text-text-primary transition-all duration-200 hover:border-gold hover:bg-gold/10 hover:text-gold focus:outline-none focus:ring-2 focus:ring-gold/25"
          >
            {mobileOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-border bg-surface lg:hidden">
          <div className="site-container py-5">
            <nav className="flex flex-col">
              {navigation.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `relative border-b border-border/70 py-3.5 text-sm font-medium transition-all duration-200 last:border-b-0 ${
                      isActive
                        ? "pl-4 text-gold-deep dark:text-gold"
                        : "text-text-primary hover:pl-2 hover:text-gold"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute left-0 top-1/2 h-5 w-[2px] -translate-y-1/2 bg-gold" />
                      )}

                      {item.label}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>

            <NavLink
              to="/rights"
              className="btn-primary mt-5 w-full"
            >
              Start Here
            </NavLink>
          </div>
        </div>
      )}
    </header>
  );
}
