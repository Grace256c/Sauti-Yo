import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Circle,
  Clock3,
  Inbox,
  Scale,
  ShieldCheck,
} from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router-dom";

/* =========================================================
   LOCAL TYPES

   These mirror the browser-session draft structures used
   by PartnerProfile.tsx and PartnerServices.tsx.

   Later, once the backend is connected, this dashboard
   should read the authenticated partner record instead.
========================================================= */

type SavedProfile = {
  organisationName?: string;
  organisationType?: string;
  registrationNumber?: string;
  yearEstablished?: string;
  description?: string;

  contactName?: string;
  contactRole?: string;
  contactEmail?: string;
  contactPhone?: string;

  headquartersDistrict?: string;
  physicalAddress?: string;
  areasServed?: string[];

  website?: string;
  publicEmail?: string;
  publicPhone?: string;
};

type SavedServices = {
  categories?: string[];
  supportTypes?: string[];
  languages?: string[];
  supportChannels?: string[];
  districtsServed?: string[];
  nationwide?: boolean;
  freeServices?: boolean;
  appointmentRequired?: boolean;
  serviceDescription?: string;
  acceptingReferrals?: boolean;
};

type SetupStatus =
  | "complete"
  | "in-progress"
  | "not-started"
  | "locked";

/* =========================================================
   SESSION STORAGE HELPERS
========================================================= */

function readSessionDraft<T>(
  key: string,
): T | null {
  try {
    const stored =
      sessionStorage.getItem(key);

    if (!stored) {
      return null;
    }

    return JSON.parse(stored) as T;
  } catch {
    return null;
  }
}

/* =========================================================
   PROFILE COMPLETION

   Uses the same required fields as PartnerProfile.tsx.
========================================================= */

function calculateProfileCompletion(
  profile: SavedProfile | null,
) {
  if (!profile) {
    return 0;
  }

  const requiredFields = [
    profile.organisationName,
    profile.organisationType,
    profile.description,
    profile.contactName,
    profile.contactRole,
    profile.contactEmail,
    profile.contactPhone,
    profile.headquartersDistrict,
    profile.physicalAddress,
  ];

  const completeFields =
    requiredFields.filter(
      (value) =>
        typeof value === "string" &&
        value.trim() !== "",
    ).length;

  return Math.round(
    (completeFields /
      requiredFields.length) *
      100,
  );
}

/* =========================================================
   SERVICES COMPLETION

   Uses the same six setup checks as PartnerServices.tsx.
========================================================= */

function calculateServicesCompletion(
  services: SavedServices | null,
) {
  if (!services) {
    return 0;
  }

  const checks = [
    (services.categories?.length ?? 0) >
      0,

    (services.supportTypes?.length ??
      0) > 0,

    (services.languages?.length ?? 0) >
      0,

    (services.supportChannels?.length ??
      0) > 0,

    Boolean(services.nationwide) ||
      (services.districtsServed?.length ??
        0) > 0,

    Boolean(
      services.serviceDescription?.trim(),
    ),
  ];

  const complete =
    checks.filter(Boolean).length;

  return Math.round(
    (complete / checks.length) * 100,
  );
}

/* =========================================================
   STATUS HELPER
========================================================= */

function getSetupStatus(
  completion: number,
): SetupStatus {
  if (completion >= 100) {
    return "complete";
  }

  if (completion > 0) {
    return "in-progress";
  }

  return "not-started";
}

/* =========================================================
   DASHBOARD
========================================================= */

export default function PartnerDashboard() {
  /*
   * Read the current browser-session drafts.
   *
   * Because the dashboard component mounts whenever the
   * partner navigates back to /partner, it picks up the most
   * recently saved Profile and Services drafts.
   */
  const profile = useMemo(
    () =>
      readSessionDraft<SavedProfile>(
        "sauti-yo-partner-profile-draft",
      ),
    [],
  );

  const services = useMemo(
    () =>
      readSessionDraft<SavedServices>(
        "sauti-yo-partner-services-draft",
      ),
    [],
  );

  const profileCompletion =
    calculateProfileCompletion(profile);

  const servicesCompletion =
    calculateServicesCompletion(services);

  /*
   * Verification is not wired yet.
   *
   * We deliberately keep it at 0 rather than pretending
   * that an organisation has submitted or passed review.
   */
  const verificationCompletion = 0;

  const overallCompletion = Math.round(
    (profileCompletion +
      servicesCompletion +
      verificationCompletion) /
      3,
  );

  const profileStatus =
    getSetupStatus(profileCompletion);

  const servicesStatus =
    getSetupStatus(servicesCompletion);

  const verificationStatus: SetupStatus =
    profileCompletion === 100 &&
    servicesCompletion === 100
      ? "not-started"
      : "locked";

  const completedSteps = [
    profileStatus,
    servicesStatus,
    verificationStatus,
  ].filter(
    (status) => status === "complete",
  ).length;

  const startedSteps = [
    profileStatus,
    servicesStatus,
    verificationStatus,
  ].filter(
    (status) =>
      status === "complete" ||
      status === "in-progress",
  ).length;

  const configuredCategories =
    services?.categories?.length ?? 0;

  const configuredSupportTypes =
    services?.supportTypes?.length ?? 0;

  const organisationName =
    profile?.organisationName?.trim();

  const nextSetupRoute =
    profileCompletion < 100
      ? "/partner/profile"
      : servicesCompletion < 100
        ? "/partner/services"
        : "/partner/profile";

  const nextSetupLabel =
    profileCompletion < 100
      ? profileCompletion > 0
        ? "Continue Profile"
        : "Start Profile"
      : servicesCompletion < 100
        ? servicesCompletion > 0
          ? "Continue Services"
          : "Set Up Services"
        : "Review Profile";

  return (
    <>
      {/* =====================================================
          PAGE HEADER
      ===================================================== */}
      <section className="border-b border-border bg-surface">
        <div className="px-5 py-8 sm:px-8 lg:px-10 lg:py-9 xl:px-12">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Partner workspace
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                {organisationName
                  ? `Welcome, ${organisationName}`
                  : "Overview"}
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Manage your organisation
                profile, services,
                verification status and
                referrals from one
                workspace.
              </p>
            </div>

            <div className="inline-flex w-fit items-center gap-2 border border-gold/30 bg-gold/5 px-4 py-2.5 text-sm">
              {overallCompletion ===
              100 ? (
                <CheckCircle2 className="h-4 w-4 text-gold" />
              ) : (
                <Clock3 className="h-4 w-4 text-gold" />
              )}

              <span className="font-semibold text-text-primary">
                {overallCompletion ===
                100
                  ? "Setup complete"
                  : "Setup in progress"}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          DASHBOARD BODY
      ===================================================== */}
      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        {/* ===================================================
            PRIMARY SETUP STATUS
        =================================================== */}
        <section className="relative overflow-hidden border border-border bg-surface">
          <div className="absolute inset-y-0 left-0 w-1 bg-gold" />

          <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                <ShieldCheck
                  className="h-6 w-6"
                  strokeWidth={1.7}
                />
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                    Organisation setup
                  </p>

                  <span className="inline-flex items-center gap-1.5 bg-gold/10 px-2.5 py-1 text-[11px] font-semibold text-gold-deep dark:text-gold">
                    {startedSteps} of 3
                    steps started
                  </span>
                </div>

                <h2 className="heading-serif mt-3 text-2xl font-semibold leading-tight text-text-primary sm:text-3xl">
                  {overallCompletion ===
                  100
                    ? "Your partner setup is complete."
                    : "Complete your partner setup"}

                  {overallCompletion <
                    100 && (
                    <span className="block text-gold-deep dark:text-gold">
                      before receiving
                      referrals.
                    </span>
                  )}
                </h2>

                <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                  Sauti Yo only sends
                  citizen referrals to
                  organisations that have
                  completed their
                  profile, described
                  their services and
                  passed the required
                  verification process.
                </p>

                {/* PROGRESS */}
                <div className="mt-6 max-w-xl">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="text-text-secondary">
                      Overall setup
                      progress
                    </span>

                    <span className="text-gold-deep dark:text-gold">
                      {overallCompletion}%
                    </span>
                  </div>

                  <div className="mt-2 h-1.5 overflow-hidden bg-border">
                    <div
                      className="h-full bg-gold transition-all duration-500"
                      style={{
                        width: `${overallCompletion}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <Link
              to={nextSetupRoute}
              className="btn-primary w-full lg:w-auto"
            >
              {nextSetupLabel}

              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        {/* ===================================================
            LIVE STATS
        =================================================== */}
        <section className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <DashboardStat
            icon={Building2}
            label="Profile"
            value={`${profileCompletion}%`}
            detail={
              profileCompletion === 100
                ? "Required details complete"
                : "Organisation details"
            }
          />

          <DashboardStat
            icon={Scale}
            label="Services"
            value={`${configuredCategories}`}
            detail={
              configuredCategories === 1
                ? "Rights category configured"
                : "Rights categories configured"
            }
          />

          <DashboardStat
            icon={Inbox}
            label="New referrals"
            value="0"
            detail="Awaiting review"
          />

          <DashboardStat
            icon={CheckCircle2}
            label="Completed"
            value="0"
            detail="Closed referrals"
          />
        </section>

        {/* ===================================================
            SECONDARY SERVICE SUMMARY
        =================================================== */}
        {(configuredCategories > 0 ||
          configuredSupportTypes >
            0) && (
          <section className="mt-5 border border-border bg-surface px-5 py-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-text-secondary">
                  Service configuration
                </p>

                <p className="mt-2 text-sm font-semibold text-text-primary">
                  {configuredCategories}{" "}
                  rights{" "}
                  {configuredCategories === 1
                    ? "category"
                    : "categories"}{" "}
                  ·{" "}
                  {configuredSupportTypes}{" "}
                  support{" "}
                  {configuredSupportTypes === 1
                    ? "type"
                    : "types"}
                </p>
              </div>

              <Link
                to="/partner/services"
                className="inline-flex items-center gap-2 text-sm font-semibold text-gold-deep transition hover:gap-3 dark:text-gold"
              >
                Review services

                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </section>
        )}

        {/* ===================================================
            MAIN GRID
        =================================================== */}
        <section className="mt-5 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          {/* SETUP CHECKLIST */}
          <article className="border border-border bg-surface p-6 sm:p-7">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Getting started
                </p>

                <h2 className="heading-serif mt-3 text-2xl font-semibold text-text-primary">
                  Prepare your
                  organisation for
                  referrals.
                </h2>
              </div>

              <span className="text-xs font-semibold text-text-secondary">
                {completedSteps} of 3
                complete
              </span>
            </div>

            <div className="mt-7">
              <SetupStep
                number="01"
                title="Complete organisation profile"
                description="Add your organisation details, contact information and operating locations."
                status={
                  profileStatus
                }
                completion={
                  profileCompletion
                }
                to="/partner/profile"
              />

              <SetupStep
                number="02"
                title="Describe your services"
                description="Define the rights issues, districts, languages and support channels your organisation handles."
                status={
                  servicesStatus
                }
                completion={
                  servicesCompletion
                }
                to="/partner/services"
              />

              <SetupStep
                number="03"
                title="Submit for verification"
                description={
                  verificationStatus ===
                  "locked"
                    ? "Complete your organisation profile and service configuration before verification becomes available."
                    : "Your profile and services are ready. Verification submission will be connected when the backend workflow is available."
                }
                status={
                  verificationStatus
                }
                completion={
                  verificationCompletion
                }
              />
            </div>
          </article>

          {/* RECENT REFERRALS */}
          <article className="border border-border bg-surface">
            <div className="flex items-start justify-between gap-5 border-b border-border p-6 sm:p-7">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Recent activity
                </p>

                <h2 className="heading-serif mt-3 text-2xl font-semibold text-text-primary">
                  Recent referrals
                </h2>
              </div>

              <Link
                to="/partner/referrals"
                className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
              >
                View all

                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="flex min-h-[310px] items-center justify-center p-7">
              <div className="max-w-sm text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gold/10 text-gold">
                  <Inbox
                    className="h-5 w-5"
                    strokeWidth={1.7}
                  />
                </div>

                <h3 className="mt-5 text-lg font-semibold text-text-primary">
                  No referrals yet
                </h3>

                <p className="mt-3 text-sm leading-6 text-text-secondary">
                  Referrals will appear
                  here after your
                  organisation is
                  verified, accepting
                  referrals and matched
                  with eligible citizen
                  requests.
                </p>

                {profileCompletion <
                100 ? (
                  <Link
                    to="/partner/profile"
                    className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-gold-deep transition hover:gap-3 dark:text-gold"
                  >
                    Complete your
                    profile

                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : servicesCompletion <
                  100 ? (
                  <Link
                    to="/partner/services"
                    className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-gold-deep transition hover:gap-3 dark:text-gold"
                  >
                    Complete your
                    services

                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : (
                  <p className="mt-6 text-xs font-semibold text-gold-deep dark:text-gold">
                    Ready for
                    verification setup
                  </p>
                )}
              </div>
            </div>
          </article>
        </section>

        {/* ===================================================
            TRUST / VERIFICATION
        =================================================== */}
        <section className="mt-5 border border-border bg-surface">
          <div className="grid gap-8 p-6 sm:p-7 lg:grid-cols-[0.72fr_1.28fr] lg:items-center">
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                <ShieldCheck
                  className="h-5 w-5"
                  strokeWidth={1.6}
                />
              </div>

              <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                Trust & verification
              </p>

              <h2 className="heading-serif mt-3 text-2xl font-semibold leading-tight text-text-primary sm:text-3xl">
                Verification protects
                <span className="block text-gold-deep dark:text-gold">
                  citizens and
                  partners.
                </span>
              </h2>
            </div>

            <div>
              <p className="text-sm leading-6 text-text-secondary sm:text-base">
                Citizens may come to
                Sauti Yo during
                sensitive legal,
                family, safety or
                community situations.
                Verification helps
                ensure referrals are
                directed only to
                organisations approved
                to participate in the
                network.
              </p>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="border-t border-border pt-4">
                  <p className="text-sm font-semibold text-text-primary">
                    Registration ≠
                    verification
                  </p>

                  <p className="mt-2 text-xs leading-5 text-text-secondary">
                    Creating a partner
                    account does not
                    automatically make
                    an organisation
                    visible to citizens.
                  </p>
                </div>

                <div className="border-t border-border pt-4">
                  <p className="text-sm font-semibold text-text-primary">
                    Verification ≠
                    automatic referrals
                  </p>

                  <p className="mt-2 text-xs leading-5 text-text-secondary">
                    Partners must also
                    be accepting
                    referrals and match
                    the citizen's
                    support needs.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

/* =========================================================
   DASHBOARD STAT
========================================================= */

function DashboardStat({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Building2;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="border border-border bg-surface px-5 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-text-secondary">
            {label}
          </p>

          <p className="mt-2 text-lg font-semibold text-text-primary">
            {value}
          </p>

          <p className="mt-1 text-xs text-text-secondary">
            {detail}
          </p>
        </div>

        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <Icon
            className="h-4 w-4"
            strokeWidth={1.7}
          />
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   SETUP STEP
========================================================= */

function SetupStep({
  number,
  title,
  description,
  status,
  completion,
  to,
}: {
  number: string;
  title: string;
  description: string;
  status: SetupStatus;
  completion: number;
  to?: string;
}) {
  const statusLabel =
    status === "complete"
      ? "Complete"
      : status === "in-progress"
        ? `${completion}% complete`
        : status === "locked"
          ? "Locked"
          : "Not started";

  const content = (
    <div
      className={[
        "group grid gap-4 border-t border-border py-5 sm:grid-cols-[auto_1fr_auto] sm:items-start",

        to
          ? "cursor-pointer"
          : "",
      ].join(" ")}
    >
      {/* STEP MARK */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-bold text-gold">
          {number}
        </span>

        <span
          className={[
            "flex h-6 w-6 items-center justify-center rounded-full border transition",

            status === "complete"
              ? "border-gold bg-gold text-[#191919]"
              : status ===
                  "in-progress"
                ? "border-gold bg-gold/10 text-gold"
                : "border-border text-text-secondary",
          ].join(" ")}
        >
          {status === "complete" ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : status ===
            "in-progress" ? (
            <Clock3 className="h-3.5 w-3.5" />
          ) : (
            <Circle className="h-3 w-3" />
          )}
        </span>
      </div>

      {/* TEXT */}
      <div>
        <h3 className="font-semibold text-text-primary">
          {title}
        </h3>

        <p className="mt-2 text-sm leading-6 text-text-secondary">
          {description}
        </p>

        {status === "in-progress" && (
          <div className="mt-3 max-w-xs">
            <div className="h-1 overflow-hidden bg-border">
              <div
                className="h-full bg-gold transition-all duration-300"
                style={{
                  width: `${completion}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* STATUS */}
      <div className="flex items-center gap-3 sm:justify-end">
        <span
          className={[
            "text-xs font-semibold",

            status === "complete" ||
            status === "in-progress"
              ? "text-gold-deep dark:text-gold"
              : "text-text-secondary",
          ].join(" ")}
        >
          {statusLabel}
        </span>

        {to && (
          <ArrowRight className="h-4 w-4 text-text-secondary transition-transform duration-200 group-hover:translate-x-1 group-hover:text-gold" />
        )}
      </div>
    </div>
  );

  if (!to) {
    return content;
  }

  return (
    <Link to={to}>
      {content}
    </Link>
  );
}