import {
  AlertCircle,
  ArrowRight,
  Building2,
  CheckCircle2,
  Circle,
  Clock3,
  Inbox,
  LoaderCircle,
  Scale,
  ShieldCheck,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Link,
} from "react-router-dom";

import {
  usePartnerAuth,
} from "../../context/PartnerAuthContext";

import {
  ApiError,
} from "../../services/api";

import {
  getPartnerOrganisation,
  getPartnerServices,
  getPartnerVerification,
} from "../../services/partners";

import {
  getReferrals,
} from "../../services/referrals";

import type {
  PartnerOrganisation,
  PartnerServiceConfiguration,
  PartnerVerification,
} from "../../services/partners";

import type {
  Referral,
} from "../../services/referrals";

/* =========================================================
   TYPES
========================================================= */

type SetupStatus =
  | "complete"
  | "in-progress"
  | "not-started"
  | "locked";

/* =========================================================
   HELPERS
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

function formatStatus(
  status: string,
) {
  return status
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}

function formatDate(
  value?: string | null,
) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  );
}

/* =========================================================
   PAGE
========================================================= */

export default function PartnerDashboard() {
  const {
    session,
  } = usePartnerAuth();

  const organisationId =
    session?.membership.organisation_id;

  const [
    organisation,
    setOrganisation,
  ] =
    useState<PartnerOrganisation | null>(
      null,
    );

  const [
    services,
    setServices,
  ] =
    useState<PartnerServiceConfiguration | null>(
      null,
    );

  const [
    verification,
    setVerification,
  ] =
    useState<PartnerVerification | null>(
      null,
    );

  const [
    referrals,
    setReferrals,
  ] =
    useState<Referral[]>(
      [],
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState("");

  /* =======================================================
     LOAD REAL BACKEND DATA
  ======================================================= */

  useEffect(() => {
    if (!organisationId) {
      setLoading(false);
      return;
    }

    const activeOrganisationId =
      organisationId;

    let active = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const [
          organisationData,
          servicesData,
          verificationData,
          referralData,
        ] =
          await Promise.all([
            getPartnerOrganisation(
              activeOrganisationId,
            ),

            getPartnerServices(
              activeOrganisationId,
            ),

            getPartnerVerification(
              activeOrganisationId,
            ),

            getReferrals(),
          ]);

        if (!active) {
          return;
        }

        setOrganisation(
          organisationData,
        );

        setServices(
          servicesData,
        );

        setVerification(
          verificationData,
        );

        setReferrals(
          referralData,
        );
      } catch (caughtError) {
        if (!active) {
          return;
        }

        if (
          caughtError instanceof
          ApiError
        ) {
          setError(
            caughtError.message,
          );
        } else {
          setError(
            "Unable to load the partner dashboard.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      active = false;
    };
  }, [organisationId]);

  /* =======================================================
     PROFILE COMPLETION
  ======================================================= */

  const profileCompletion =
    useMemo(() => {
      if (!organisation) {
        return 0;
      }

      const requiredValues = [
        organisation
          .support_service
          .name,

        organisation
          .organisation_type,

        organisation
          .support_service
          .description,

        organisation
          .headquarters_district,

        organisation
          .physical_address,
      ];

      const complete =
        requiredValues.filter(
          (value) =>
            String(
              value ?? "",
            ).trim() !== "",
        ).length;

      return Math.round(
        (
          complete /
          requiredValues.length
        ) * 100,
      );
    }, [organisation]);

  /* =======================================================
     SERVICES COMPLETION
  ======================================================= */

  const servicesCompletion =
    useMemo(() => {
      if (!services) {
        return 0;
      }

      const checks = [
        services
          .rights_categories
          .length > 0,

        services
          .support_types
          .length > 0,

        services
          .service_description
          .trim() !== "",

        services
          .languages
          .length > 0,

        services
          .support_channels
          .length > 0,

        services.nationwide ||
          services
            .districts_served
            .length > 0,
      ];

      const complete =
        checks.filter(
          Boolean,
        ).length;

      return Math.round(
        (
          complete /
          checks.length
        ) * 100,
      );
    }, [services]);

  /* =======================================================
     VERIFICATION
  ======================================================= */

  const verificationCompletion =
    useMemo(() => {
      if (!verification) {
        return 0;
      }

      if (
        verification.status ===
        "verified"
      ) {
        return 100;
      }

      if (
        [
          "submitted",
          "under_review",
        ].includes(
          verification.status,
        )
      ) {
        return 80;
      }

      return 25;
    }, [verification]);

  const verificationStatus:
    SetupStatus =
      verification?.status ===
      "verified"
        ? "complete"
        : verification
          ? "in-progress"
          : profileCompletion ===
                100 &&
              servicesCompletion ===
                100
            ? "not-started"
            : "locked";

  const profileStatus =
    getSetupStatus(
      profileCompletion,
    );

  const servicesStatus =
    getSetupStatus(
      servicesCompletion,
    );

  const completedSteps = [
    profileStatus,
    servicesStatus,
    verificationStatus,
  ].filter(
    (status) =>
      status === "complete",
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

  const overallCompletion =
    Math.round(
      (
        profileCompletion +
        servicesCompletion +
        verificationCompletion
      ) / 3,
    );

  /* =======================================================
     REFERRALS
  ======================================================= */

  const newReferrals =
    referrals.filter(
      (referral) =>
        referral.status === "new",
    ).length;

  const completedReferrals =
    referrals.filter(
      (referral) =>
        referral.status ===
        "completed",
    ).length;

  const recentReferrals =
    useMemo(
      () =>
        [...referrals]
          .sort(
            (a, b) =>
              new Date(
                b.created_at ?? 0,
              ).getTime() -
              new Date(
                a.created_at ?? 0,
              ).getTime(),
          )
          .slice(0, 3),
      [referrals],
    );

  const configuredCategories =
    services
      ?.rights_categories
      .length ?? 0;

  const configuredSupportTypes =
    services
      ?.support_types
      .length ?? 0;

  const organisationName =
    organisation
      ?.support_service
      .name
      ?.trim();

  /* =======================================================
     NEXT SETUP STEP
  ======================================================= */

  const nextSetupRoute =
    profileCompletion < 100
      ? "/partner/profile"
      : servicesCompletion < 100
        ? "/partner/services"
        : verification?.status !==
            "verified"
          ? "/partner/verification"
          : "/partner/referrals";

  const nextSetupLabel =
    profileCompletion < 100
      ? "Complete Profile"
      : servicesCompletion < 100
        ? "Complete Services"
        : verification?.status !==
            "verified"
          ? "View Verification"
          : "View Referrals";

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center px-5">
        <div className="text-center">
          <LoaderCircle className="mx-auto h-6 w-6 animate-spin text-gold" />

          <p className="mt-4 text-sm text-text-secondary">
            Loading partner dashboard...
          </p>
        </div>
      </div>
    );
  }

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
          BODY
      ===================================================== */}

      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">

        {error && (
          <div className="mb-5 flex items-start gap-3 border border-danger/30 bg-danger/5 p-4">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />

            <p className="text-sm leading-6 text-danger">
              {error}
            </p>
          </div>
        )}

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
                      before full referral
                      participation.
                    </span>
                  )}
                </h2>

                <p className="mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                  Profile, services and
                  verification information
                  shown here now comes
                  directly from the Sauti Yo
                  backend.
                </p>

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
                        width:
                          `${overallCompletion}%`,
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
              profileCompletion ===
              100
                ? "Required details complete"
                : "Organisation details"
            }
          />

          <DashboardStat
            icon={Scale}
            label="Services"
            value={`${configuredCategories}`}
            detail={
              configuredCategories ===
              1
                ? "Rights category configured"
                : "Rights categories configured"
            }
          />

          <DashboardStat
            icon={Inbox}
            label="New referrals"
            value={`${newReferrals}`}
            detail="Awaiting review"
          />

          <DashboardStat
            icon={CheckCircle2}
            label="Completed"
            value={`${completedReferrals}`}
            detail="Completed referrals"
          />
        </section>

        {/* ===================================================
            SERVICE SUMMARY
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
                  {configuredCategories ===
                  1
                    ? "category"
                    : "categories"}{" "}
                  ·{" "}
                  {configuredSupportTypes}{" "}
                  support{" "}
                  {configuredSupportTypes ===
                  1
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
                title="Verification"
                description={
                  verification
                    ? `Current verification status: ${formatStatus(
                        verification.status,
                      )}.`
                    : verificationStatus ===
                        "locked"
                      ? "Complete your profile and services before submitting for verification."
                      : "Your organisation is ready to submit for verification."
                }
                status={
                  verificationStatus
                }
                completion={
                  verificationCompletion
                }
                to="/partner/verification"
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

            {recentReferrals.length >
            0 ? (
              <div className="divide-y divide-border">
                {recentReferrals.map(
                  (referral) => (
                    <Link
                      key={
                        referral.id
                      }
                      to={`/partner/referrals/${referral.id}`}
                      className="group block p-5 transition hover:bg-background sm:p-6"
                    >
                      <div className="flex items-start justify-between gap-5">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-semibold text-text-primary">
                              {referral.reference ||
                                `Referral #${referral.id}`}
                            </p>

                            <span className="border border-gold/30 bg-gold/5 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.1em] text-gold-deep dark:text-gold">
                              {formatStatus(
                                referral.status,
                              )}
                            </span>
                          </div>

                          <p className="mt-2 line-clamp-2 text-sm leading-6 text-text-secondary">
                            {referral.summary ||
                              "No referral summary provided."}
                          </p>

                          <p className="mt-3 text-xs text-text-secondary">
                            {referral.district ||
                              "District not specified"}
                            {" · "}
                            {formatDate(
                              referral.created_at,
                            )}
                          </p>
                        </div>

                        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-text-secondary transition group-hover:translate-x-1 group-hover:text-gold" />
                      </div>
                    </Link>
                  ),
                )}
              </div>
            ) : (
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
                    New referrals assigned
                    to this organisation
                    will appear here.
                  </p>
                </div>
              </div>
            )}
          </article>
        </section>

        {/* ===================================================
            TRUST
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
                    verified.
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
      : status ===
          "in-progress"
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
          {status ===
          "complete" ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : status ===
            "in-progress" ? (
            <Clock3 className="h-3.5 w-3.5" />
          ) : (
            <Circle className="h-3 w-3" />
          )}
        </span>
      </div>

      <div>
        <h3 className="font-semibold text-text-primary">
          {title}
        </h3>

        <p className="mt-2 text-sm leading-6 text-text-secondary">
          {description}
        </p>

        {status ===
          "in-progress" && (
          <div className="mt-3 max-w-xs">
            <div className="h-1 overflow-hidden bg-border">
              <div
                className="h-full bg-gold transition-all duration-300"
                style={{
                  width:
                    `${completion}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

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
