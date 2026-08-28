import {
  ArrowLeft,
  Building2,
  Inbox,
  LayoutDashboard,
  Menu,
  Moon,
  Scale,
  Settings,
  ShieldCheck,
  Sun,
  X,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";
import {
  Link,
  NavLink,
  Outlet,
} from "react-router-dom";

import sautiYoLogo from "../../assets/branding/sauti-yo-logo-horizontal.png";
import sautiYoLogoLight from "../../assets/branding/sauti-yo-logo-light.png";

type PortalTheme =
  | "light"
  | "dark";

const THEME_STORAGE_KEY =
  "sauti-yo-partner-theme";

const navigation = [
  {
    label: "Overview",
    to: "/partner",
    icon: LayoutDashboard,
    end: true,
  },
  {
    label: "Organisation Profile",
    to: "/partner/profile",
    icon: Building2,
  },
  {
    label: "Services",
    to: "/partner/services",
    icon: Scale,
  },
  {
    label: "Verification",
    to: "/partner/verification",
    icon: ShieldCheck,
  },
  {
    label: "Referrals",
    to: "/partner/referrals",
    icon: Inbox,
  },
  {
    label: "Settings",
    to: "/partner/settings",
    icon: Settings,
  },
];

function getInitialTheme(): PortalTheme {
  try {
    const saved =
      localStorage.getItem(
        THEME_STORAGE_KEY,
      );

    if (
      saved === "light" ||
      saved === "dark"
    ) {
      return saved;
    }

    if (
      window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches
    ) {
      return "dark";
    }

    return "light";
  } catch {
    return "light";
  }
}

export default function PartnerShell() {
  const [
    mobileOpen,
    setMobileOpen,
  ] = useState(false);

  const [theme, setTheme] =
    useState<PortalTheme>(
      getInitialTheme,
    );

  useEffect(() => {
    const root =
      document.documentElement;

    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }

    try {
      localStorage.setItem(
        THEME_STORAGE_KEY,
        theme,
      );
    } catch {
      // Ignore storage errors.
    }
  }, [theme]);

  const setPortalTheme = (
    nextTheme: PortalTheme,
  ) => {
    setTheme(nextTheme);
  };

  const activeLogo =
    theme === "dark"
      ? sautiYoLogoLight
      : sautiYoLogo;

  return (
    <div className="min-h-screen bg-background text-text-primary transition-colors duration-300">
      {/* MOBILE HEADER */}
      <header className="sticky top-0 z-40 flex min-h-[72px] items-center justify-between border-b border-border bg-surface/95 px-5 backdrop-blur transition-colors duration-300 lg:hidden">
        <Link
          to="/partner"
          className="flex min-w-0 items-center gap-3"
        >
          <div className="flex shrink-0 flex-col items-start justify-center">
            <img
              src={activeLogo}
              alt="Sauti Yo"
              className="block h-auto w-[132px] object-contain object-left sm:w-[145px]"
            />

            <span className="mt-0.5 pl-0.5 text-[8px] font-bold uppercase leading-none tracking-[0.18em] text-gold-deep dark:text-gold">
              Know. Act. Be Heard.
            </span>
          </div>

          <div className="h-9 w-px bg-border" />

          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
              Partner Portal
            </p>

            <p className="mt-0.5 truncate text-xs text-text-secondary">
              Organisation workspace
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() =>
              setPortalTheme(
                theme === "light"
                  ? "dark"
                  : "light",
              )
            }
            className="flex h-10 w-10 items-center justify-center border border-border bg-background text-text-primary transition hover:border-gold hover:text-gold"
            aria-label={
              theme === "light"
                ? "Switch to dark mode"
                : "Switch to light mode"
            }
          >
            {theme === "light" ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </button>

          <button
            type="button"
            onClick={() =>
              setMobileOpen(
                (current) =>
                  !current,
              )
            }
            className="flex h-10 w-10 items-center justify-center border border-border bg-background text-text-primary transition hover:border-gold"
            aria-label="Toggle partner navigation"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </header>

      {/* MOBILE NAVIGATION */}
      {mobileOpen && (
        <div className="fixed inset-x-0 bottom-0 top-[72px] z-30 overflow-y-auto bg-surface transition-colors duration-300 lg:hidden">
          <div className="flex min-h-full flex-col">
            <div className="flex-1 px-5 py-6">
              <PartnerNavigation
                onNavigate={() =>
                  setMobileOpen(false)
                }
              />
            </div>

            <div className="border-t border-border bg-surface-soft p-5">
              <PartnerThemeControl
                theme={theme}
                onChange={
                  setPortalTheme
                }
              />

              <div className="mt-4">
                <PartnerStatus />
              </div>

              <Link
                to="/"
                onClick={() =>
                  setMobileOpen(false)
                }
                className="mt-4 flex min-h-11 items-center gap-2 px-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Sauti Yo
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* DESKTOP PORTAL */}
      <div className="lg:grid lg:min-h-screen lg:grid-cols-[264px_minmax(0,1fr)]">
        <aside className="hidden border-r border-border bg-surface transition-colors duration-300 lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
          {/* BRAND */}
          <div className="border-b border-border px-6 py-6">
            <Link
              to="/partner"
              className="block"
            >
              <div className="flex flex-col items-start">
                <img
                  src={activeLogo}
                  alt="Sauti Yo"
                  className="block h-auto w-[178px] object-contain object-left"
                />

                <span className="mt-1 pl-0.5 text-[9px] font-bold uppercase leading-none tracking-[0.2em] text-gold-deep dark:text-gold">
                  Know. Act. Be Heard.
                </span>
              </div>

              <div className="mt-5 flex items-center gap-3">
                <span className="h-px w-8 bg-gold" />

                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Partner Portal
                </p>
              </div>

              <p className="mt-2 max-w-[195px] text-xs leading-5 text-text-secondary">
                Organisation workspace
                for services,
                verification and
                referrals.
              </p>
            </Link>
          </div>

          {/* NAVIGATION */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <PartnerNavigation />
          </div>

          {/* BOTTOM CONTROLS */}
          <div className="border-t border-border bg-surface-soft p-4">
            <PartnerThemeControl
              theme={theme}
              onChange={setPortalTheme}
            />

            <div className="mt-4">
              <PartnerStatus />
            </div>

            <Link
              to="/"
              className="mt-4 flex min-h-11 items-center gap-2 rounded-sm px-3 text-sm font-semibold text-text-secondary transition hover:bg-background hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />

              Back to Sauti Yo
            </Link>
          </div>
        </aside>

        <main className="min-w-0 bg-background transition-colors duration-300">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function PartnerNavigation({
  onNavigate,
}: {
  onNavigate?: () => void;
}) {
  return (
    <nav aria-label="Partner workspace navigation">
      <p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-text-secondary">
        Workspace
      </p>

      <div className="mt-3 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onNavigate}
              className={({
                isActive,
              }) =>
                [
                  "group relative flex min-h-12 items-center gap-3 rounded-sm px-3 text-sm font-semibold transition-all duration-200",

                  isActive
                    ? "bg-gold/10 text-text-primary"
                    : "text-text-secondary hover:bg-background hover:text-text-primary",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-2 left-0 top-2 w-[2px] bg-gold"
                    />
                  )}

                  <span
                    className={[
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all duration-200",

                      isActive
                        ? "bg-gold/15 text-gold"
                        : "text-text-secondary group-hover:bg-gold/10 group-hover:text-gold",
                    ].join(" ")}
                  >
                    <Icon
                      className="h-[17px] w-[17px]"
                      strokeWidth={1.7}
                    />
                  </span>

                  <span className="min-w-0">
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}

function PartnerThemeControl({
  theme,
  onChange,
}: {
  theme: PortalTheme;
  onChange: (
    theme: PortalTheme,
  ) => void;
}) {
  return (
    <div className="border border-border bg-background p-1.5">
      <div className="grid grid-cols-2 gap-1">
        <button
          type="button"
          onClick={() =>
            onChange("light")
          }
          className={[
            "flex min-h-9 items-center justify-center gap-2 px-2 text-xs font-semibold transition",

            theme === "light"
              ? "bg-surface text-text-primary shadow-sm"
              : "text-text-secondary hover:bg-surface hover:text-text-primary",
          ].join(" ")}
          aria-pressed={
            theme === "light"
          }
        >
          <Sun className="h-3.5 w-3.5" />
          Light
        </button>

        <button
          type="button"
          onClick={() =>
            onChange("dark")
          }
          className={[
            "flex min-h-9 items-center justify-center gap-2 px-2 text-xs font-semibold transition",

            theme === "dark"
              ? "bg-surface text-gold shadow-sm"
              : "text-text-secondary hover:bg-surface hover:text-text-primary",
          ].join(" ")}
          aria-pressed={
            theme === "dark"
          }
        >
          <Moon className="h-3.5 w-3.5" />
          Dark
        </button>
      </div>
    </div>
  );
}

function PartnerStatus() {
  return (
    <div className="border border-border bg-background p-4 transition-colors duration-300">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck
            className="h-4 w-4 text-gold"
            strokeWidth={1.7}
          />

          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-text-secondary">
            Verification
          </p>
        </div>

        <span
          className="h-2 w-2 rounded-full bg-gold"
          aria-hidden="true"
        />
      </div>

      <p className="mt-3 text-sm font-semibold text-text-primary">
        Organisation setup
      </p>

      <p className="mt-2 text-xs leading-5 text-text-secondary">
        Complete your profile,
        services and verification
        request before becoming
        eligible for referrals.
      </p>

      <Link
        to="/partner/verification"
        className="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-gold-deep transition hover:gap-3 dark:text-gold"
      >
        View verification
        <ShieldCheck className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}