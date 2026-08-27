import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  useLocation,
} from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ChevronDown,
  Globe2,
  Menu,
  Moon,
  Sun,
  X,
} from "lucide-react";

import logo from "../../assets/branding/sauti-yo-logo-horizontal.png";
import logoLight from "../../assets/branding/sauti-yo-logo-light.png";

const languages = [
  { code: "en", label: "English" },
  { code: "lg", label: "Luganda" },
  { code: "sw", label: "Kiswahili" },
  { code: "nyn", label: "Runyankole" },
];

const navigation = [
  { to: "/", key: "nav.home" },
  { to: "/about", key: "nav.about" },
  { to: "/rights", key: "nav.rights" },
  { to: "/how-it-works", key: "nav.howItWorks" },
  { to: "/access", key: "nav.access" },
  { to: "/community", key: "nav.community" },
  { to: "/support", key: "nav.support" },
];

export default function Header() {
  const { t, i18n } = useTranslation();
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

  const changeLanguage = (language: string) => {
    i18n.changeLanguage(language);
    setMobileOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/95 shadow-[0_4px_20px_rgba(0,0,0,0.04)] backdrop-blur-md">
      <div className="site-container flex min-h-[74px] items-center justify-between gap-4">
        {/* Logo */}
        <Link
          to="/"
          aria-label="Sauti Yo home"
          className="flex min-w-0 shrink-0 items-center"
        >
          <div className="flex h-[54px] w-[150px] items-center overflow-hidden sm:w-[165px] xl:w-[178px]">
            <img
              src={darkMode ? logoLight : logo}
              alt="Sauti Yo"
              className="max-h-[48px] w-full object-contain object-left"
            />
          </div>
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
                    {t(item.key)}
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
          <div className="relative">
            <Globe2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />

            <select
              value={i18n.language}
              onChange={(event) =>
                changeLanguage(event.target.value)
              }
              aria-label="Select language"
              className="h-11 min-w-[132px] appearance-none rounded-md border border-border bg-surface py-2 pl-9 pr-9 text-sm font-medium text-text-primary outline-none transition-all duration-200 hover:border-gold focus:border-gold focus:ring-2 focus:ring-gold/25"
            >
              {languages.map((language) => (
                <option
                  key={language.code}
                  value={language.code}
                  className="bg-surface text-text-primary"
                >
                  {language.label}
                </option>
              ))}
            </select>

            <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
          </div>

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
            {t("common.startHere")}
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

                      {t(item.key)}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>

            <div className="mt-5">
              <p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-text-secondary">
                <Globe2 className="h-4 w-4" />
                {t("common.language")}
              </p>

              <div className="grid grid-cols-2 gap-2">
                {languages.map((language) => {
                  const active =
                    i18n.language === language.code;

                  return (
                    <button
                      key={language.code}
                      type="button"
                      onClick={() =>
                        changeLanguage(language.code)
                      }
                      className={`min-h-11 rounded-md border px-3 py-2 text-left text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gold/25 ${
                        active
                          ? "border-gold bg-gold/10 text-gold-deep dark:text-gold"
                          : "border-border bg-surface text-text-secondary hover:border-gold hover:bg-gold/5 hover:text-gold"
                      }`}
                    >
                      {language.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <NavLink
              to="/rights"
              className="btn-primary mt-5 w-full"
            >
              {t("common.startHere")}
            </NavLink>
          </div>
        </div>
      )}
    </header>
  );
}