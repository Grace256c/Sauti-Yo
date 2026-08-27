import {
  ArrowLeft,
  ArrowRight,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import sautiYoLogo from "../../assets/branding/sauti-yo-logo-horizontal.png";

import {
  usePartnerAuth,
} from "../../context/PartnerAuthContext";

import {
  ApiError,
} from "../../services/api";

export default function PartnerLogin() {
  const {
    authenticated,
    loading,
    login,
  } = usePartnerAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-5 text-text-primary">
        <p className="text-sm text-text-secondary">
          Checking partner session...
        </p>
      </div>
    );
  }

  if (authenticated) {
    return (
      <Navigate
        to="/partner"
        replace
      />
    );
  }

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      await login({
        username,
        password,
      });

      const state =
        location.state as
          | {
              from?: string;
            }
          | null;

      navigate(
        state?.from ??
          "/partner",
        {
          replace: true,
        },
      );
    } catch (caughtError) {
      if (
        caughtError instanceof
        ApiError
      ) {
        setError(
          caughtError.message,
        );
      } else {
        setError(
          "Unable to sign in right now.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-background text-text-primary">
      <div className="grid min-h-screen lg:grid-cols-[0.9fr_1.1fr]">
        {/* BRAND PANEL */}
        <section className="hidden border-r border-border bg-surface-soft lg:flex lg:flex-col lg:justify-between lg:p-12 xl:p-16">
          <Link
            to="/"
            className="inline-flex w-fit"
          >
            <img
              src={sautiYoLogo}
              alt="Sauti Yo"
              className="h-11 w-auto object-contain"
            />
          </Link>

          <div className="max-w-lg">
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Partner Portal
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold leading-tight text-text-primary xl:text-5xl">
              Support citizens through
              <span className="block text-gold-deep dark:text-gold">
                a trusted partner network.
              </span>
            </h1>

            <p className="mt-6 max-w-md text-base leading-7 text-text-secondary">
              Manage your organisation,
              services, verification and
              referrals from one secure
              workspace.
            </p>
          </div>

          <div className="flex items-start gap-3 border-t border-border pt-6">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

            <p className="max-w-md text-xs leading-5 text-text-secondary">
              Partner access is limited
              to authorised members of
              participating organisations.
            </p>
          </div>
        </section>

        {/* LOGIN */}
        <section className="flex items-center justify-center px-5 py-12 sm:px-8 lg:px-12">
          <div className="w-full max-w-md">
            <div className="lg:hidden">
              <img
                src={sautiYoLogo}
                alt="Sauti Yo"
                className="h-10 w-auto object-contain"
              />
            </div>

            <div className="mt-10 lg:mt-0">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                <LockKeyhole
                  className="h-5 w-5"
                  strokeWidth={1.7}
                />
              </div>

              <p className="mt-6 text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Secure access
              </p>

              <h2 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Sign in to your workspace
              </h2>

              <p className="mt-4 text-sm leading-6 text-text-secondary">
                Use the account connected
                to your partner organisation.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="mt-8 space-y-5"
            >
              <div>
                <label
                  htmlFor="username"
                  className="text-sm font-semibold text-text-primary"
                >
                  Username
                </label>

                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(event) =>
                    setUsername(
                      event.target.value,
                    )
                  }
                  className="mt-2 min-h-12 w-full border border-border bg-surface px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="text-sm font-semibold text-text-primary"
                >
                  Password
                </label>

                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) =>
                    setPassword(
                      event.target.value,
                    )
                  }
                  className="mt-2 min-h-12 w-full border border-border bg-surface px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                />
              </div>

              {error && (
                <div className="border border-danger/30 bg-danger/5 p-4">
                  <p className="text-sm leading-6 text-danger">
                    {error}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="btn-primary w-full"
              >
                {submitting
                  ? "Signing in..."
                  : "Sign In"}

                {!submitting && (
                  <ArrowRight className="h-4 w-4" />
                )}
              </button>
            </form>

            <Link
              to="/"
              className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />

              Back to Sauti Yo
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
