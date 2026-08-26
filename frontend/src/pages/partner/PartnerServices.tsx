import {
  AlertCircle,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  Globe2,
  LoaderCircle,
  MapPin,
  Save,
  Scale,
  ShieldCheck,
  Users,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
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
  getPartnerServices,
  updatePartnerServices,
} from "../../services/partners";

/* =========================================================
   TYPES
========================================================= */

type ServiceForm = {
  rightsCategories: string[];
  supportTypes: string[];

  serviceDescription: string;

  languages: string[];
  supportChannels: string[];

  nationwide: boolean;
  districtsServed: string[];

  freeServices: boolean;
  appointmentRequired: boolean;
  acceptingReferrals: boolean;

  weeklyReferralLimit: string;
  availabilityNote: string;
};

/* =========================================================
   OPTIONS
========================================================= */

const rightsCategoryOptions = [
  {
    value: "work-employment",
    title: "Work & Employment",
    description:
      "Employment rights, pay, dismissal, workplace treatment and labour-related problems.",
    icon: BriefcaseBusiness,
  },
  {
    value: "safety-protection",
    title: "Safety & Protection",
    description:
      "Violence, threats, harassment, personal safety and protection concerns.",
    icon: ShieldCheck,
  },
  {
    value: "land-housing",
    title: "Land & Housing",
    description:
      "Land ownership, tenancy, eviction, housing and property-related disputes.",
    icon: MapPin,
  },
  {
    value: "family-inheritance",
    title: "Family & Inheritance",
    description:
      "Family disputes, child-related concerns, inheritance and succession issues.",
    icon: Users,
  },
  {
    value: "public-services",
    title: "Public Services",
    description:
      "Access to public institutions, administrative services and official processes.",
    icon: Scale,
  },
  {
    value: "community-discrimination",
    title: "Community & Discrimination",
    description:
      "Discrimination, exclusion, community disputes and rights within the community.",
    icon: Globe2,
  },
];

const supportTypeOptions = [
  {
    value: "work-labour-support",
    title: "Work & Labour Support",
    description:
      "Support for workplace concerns including pay, dismissal, employment agreements and labour disputes.",
  },
  {
    value: "safety-protection-support",
    title: "Safety & Protection Support",
    description:
      "Support pathways for situations involving violence, abuse, threats, harassment or personal safety.",
  },
  {
    value: "land-housing-support",
    title: "Land & Housing Support",
    description:
      "Support for land ownership, tenancy, eviction, boundary and other property-related concerns.",
  },
  {
    value: "family-inheritance-support",
    title: "Family & Inheritance Support",
    description:
      "Support for family matters including inheritance, children, relationships and family responsibilities.",
  },
  {
    value: "public-service-support",
    title: "Public Service Support",
    description:
      "Support for difficulties involving public institutions, administrative decisions, complaints or access to services.",
  },
  {
    value: "community-rights-support",
    title: "Community & Rights Support",
    description:
      "Support where a person is experiencing discrimination, exclusion, harassment or another community-rights concern.",
  },
  {
    value: "general-legal-support",
    title: "General Legal Support",
    description:
      "A broader pathway for situations that may require legal information, advice or representation beyond one specific category.",
  },
];

const languageOptions = [
  "English",
  "Luganda",
  "Runyankole",
  "Lusoga",
  "Acholi",
  "Ateso",
  "Langi",
  "Other",
];

const supportChannelOptions = [
  {
    value: "in_person",
    label: "In person",
    description:
      "Citizens can physically visit or meet your organisation.",
  },
  {
    value: "phone",
    label: "Phone",
    description:
      "Citizens can receive support through a phone call.",
  },
  {
    value: "remote",
    label: "Remote / digital",
    description:
      "Support can be provided through online or other remote channels.",
  },
];

const districtOptions = [
  "Kampala",
  "Wakiso",
  "Mukono",
  "Jinja",
  "Masaka",
  "Mbarara",
  "Gulu",
  "Lira",
  "Mbale",
  "Fort Portal",
  "Other",
];

const initialForm: ServiceForm = {
  rightsCategories: [],
  supportTypes: [],

  serviceDescription: "",

  languages: [],
  supportChannels: [],

  nationwide: false,
  districtsServed: [],

  freeServices: false,
  appointmentRequired: false,
  acceptingReferrals: false,

  weeklyReferralLimit: "",
  availabilityNote: "",
};

/* =========================================================
   PAGE
========================================================= */

export default function PartnerServices() {
  const {
    session,
  } = usePartnerAuth();

  const organisationId =
    session?.membership.organisation_id;

  const [
    form,
    setForm,
  ] =
    useState<ServiceForm>(
      initialForm,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    saving,
    setSaving,
  ] =
    useState(false);

  const [
    saved,
    setSaved,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState("");

  /* =======================================================
     LOAD FROM DJANGO
  ======================================================= */

  useEffect(() => {
    if (!organisationId) {
      setLoading(false);
      return;
    }

    const activeOrganisationId =
      organisationId;

    let active = true;

    async function loadServices() {
      setLoading(true);
      setError("");

      try {
        const data =
          await getPartnerServices(
            activeOrganisationId,
          );

        if (!active) {
          return;
        }

        setForm({
          rightsCategories:
            data.rights_categories ?? [],

          supportTypes:
            data.support_types ?? [],

          serviceDescription:
            data.service_description ?? "",

          languages:
            data.languages ?? [],

          supportChannels:
            data.support_channels ?? [],

          nationwide:
            data.nationwide ?? false,

          districtsServed:
            data.districts_served ?? [],

          freeServices:
            data.free_services ?? false,

          appointmentRequired:
            data.appointment_required ?? false,

          acceptingReferrals:
            data.accepting_referrals ?? false,

          weeklyReferralLimit:
            data.weekly_referral_limit !== null &&
            data.weekly_referral_limit !== undefined
              ? String(
                  data.weekly_referral_limit,
                )
              : "",

          availabilityNote:
            data.availability_note ?? "",
        });
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
            "Unable to load your service configuration.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadServices();

    return () => {
      active = false;
    };
  }, [organisationId]);

  /* =======================================================
     COMPLETION
  ======================================================= */

  const completion =
    useMemo(() => {
      const checks = [
        form.rightsCategories.length > 0,
        form.supportTypes.length > 0,
        form.serviceDescription.trim() !== "",
        form.languages.length > 0,
        form.supportChannels.length > 0,
        form.nationwide ||
          form.districtsServed.length > 0,
      ];

      return Math.round(
        (
          checks.filter(Boolean).length /
          checks.length
        ) * 100,
      );
    }, [form]);

  /* =======================================================
     HELPERS
  ======================================================= */

  function toggleArrayValue(
    field:
      | "rightsCategories"
      | "supportTypes"
      | "languages"
      | "supportChannels"
      | "districtsServed",
    value: string,
  ) {
    setForm((current) => {
      const list =
        current[field];

      const selected =
        list.includes(value);

      return {
        ...current,
        [field]:
          selected
            ? list.filter(
                (item) =>
                  item !== value,
              )
            : [
                ...list,
                value,
              ],
      };
    });

    setSaved(false);
  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function handleSave() {
    if (!organisationId) {
      setError(
        "No partner organisation is connected to this account.",
      );
      return;
    }

    let weeklyReferralLimit:
      | number
      | null = null;

    if (
      form.weeklyReferralLimit.trim()
    ) {
      const parsed =
        Number(
          form.weeklyReferralLimit,
        );

      if (
        !Number.isInteger(parsed) ||
        parsed < 0
      ) {
        setError(
          "Weekly referral limit must be a whole number of zero or more.",
        );
        return;
      }

      weeklyReferralLimit =
        parsed;
    }

    setSaving(true);
    setSaved(false);
    setError("");

    try {
      const data =
        await updatePartnerServices(
          organisationId,
          {
            rights_categories:
              form.rightsCategories,

            support_types:
              form.supportTypes,

            service_description:
              form.serviceDescription.trim(),

            languages:
              form.languages,

            support_channels:
              form.supportChannels,

            nationwide:
              form.nationwide,

            districts_served:
              form.nationwide
                ? []
                : form.districtsServed,

            free_services:
              form.freeServices,

            appointment_required:
              form.appointmentRequired,

            accepting_referrals:
              form.acceptingReferrals,

            weekly_referral_limit:
              weeklyReferralLimit,

            availability_note:
              form.availabilityNote.trim(),
          },
        );

      setForm({
        rightsCategories:
          data.rights_categories ?? [],

        supportTypes:
          data.support_types ?? [],

        serviceDescription:
          data.service_description ?? "",

        languages:
          data.languages ?? [],

        supportChannels:
          data.support_channels ?? [],

        nationwide:
          data.nationwide ?? false,

        districtsServed:
          data.districts_served ?? [],

        freeServices:
          data.free_services ?? false,

        appointmentRequired:
          data.appointment_required ?? false,

        acceptingReferrals:
          data.accepting_referrals ?? false,

        weeklyReferralLimit:
          data.weekly_referral_limit !== null &&
          data.weekly_referral_limit !== undefined
            ? String(
                data.weekly_referral_limit,
              )
            : "",

        availabilityNote:
          data.availability_note ?? "",
      });

      setSaved(true);

      window.setTimeout(() => {
        setSaved(false);
      }, 3000);
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
          "Unable to save your service configuration.",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center px-5">
        <div className="text-center">
          <LoaderCircle className="mx-auto h-6 w-6 animate-spin text-gold" />

          <p className="mt-4 text-sm text-text-secondary">
            Loading service
            configuration...
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* HEADER */}

      <section className="border-b border-border bg-surface">
        <div className="px-5 py-8 sm:px-8 lg:px-10 lg:py-9 xl:px-12">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Partner services
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Services
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Tell Sauti Yo which
                rights issues your
                organisation handles,
                where you operate and
                how citizens can receive
                support.
              </p>
            </div>

            <div className="min-w-[220px]">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-text-secondary">
                  Service setup
                </span>

                <span className="text-gold-deep dark:text-gold">
                  {completion}%
                </span>
              </div>

              <div className="mt-2 h-1.5 overflow-hidden bg-border">
                <div
                  className="h-full bg-gold transition-all"
                  style={{
                    width:
                      `${completion}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">

          {error && (
            <div className="mb-6 flex items-start gap-3 border border-danger/30 bg-danger/5 p-4">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />

              <p className="text-sm leading-6 text-danger">
                {error}
              </p>
            </div>
          )}

          <section className="border border-border bg-surface p-5 sm:p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                <ShieldCheck className="h-5 w-5" />
              </div>

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Referral matching
                </p>

                <h2 className="mt-2 font-semibold text-text-primary">
                  Accurate service
                  information improves
                  matching.
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                  These details help
                  Sauti Yo determine
                  whether your
                  organisation is an
                  appropriate match for
                  a citizen's issue,
                  location, language and
                  preferred support
                  method.
                </p>
              </div>
            </div>
          </section>

          {/* RIGHTS */}

          <ServiceSection
            eyebrow="Section 01"
            title="Rights issues handled"
            description="Select the citizen-facing rights categories your organisation is genuinely equipped to support."
          >
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {rightsCategoryOptions.map(
                (item) => {
                  const Icon =
                    item.icon;

                  const selected =
                    form.rightsCategories.includes(
                      item.value,
                    );

                  return (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() =>
                        toggleArrayValue(
                          "rightsCategories",
                          item.value,
                        )
                      }
                      className={[
                        "min-h-[150px] border p-5 text-left transition",
                        selected
                          ? "border-gold bg-gold/5"
                          : "border-border bg-background hover:border-gold/60",
                      ].join(" ")}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gold/10 text-gold">
                          <Icon className="h-4 w-4" />
                        </div>

                        <SelectionMark
                          active={
                            selected
                          }
                        />
                      </div>

                      <h3 className="mt-4 font-semibold text-text-primary">
                        {item.title}
                      </h3>

                      <p className="mt-2 text-xs leading-5 text-text-secondary">
                        {item.description}
                      </p>
                    </button>
                  );
                },
              )}
            </div>
          </ServiceSection>

          {/* SUPPORT TYPES */}

          <ServiceSection
            eyebrow="Section 02"
            title="Types of support provided"
            description="Select the support pathways that best describe what your organisation actually provides."
          >
            <div className="grid gap-4 md:grid-cols-2">
              {supportTypeOptions.map(
                (item) => {
                  const selected =
                    form.supportTypes.includes(
                      item.value,
                    );

                  return (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() =>
                        toggleArrayValue(
                          "supportTypes",
                          item.value,
                        )
                      }
                      className={[
                        "min-h-[145px] border p-5 text-left transition",
                        selected
                          ? "border-gold bg-gold/5"
                          : "border-border bg-background hover:border-gold/60",
                      ].join(" ")}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <h3 className="font-semibold text-text-primary">
                          {item.title}
                        </h3>

                        <SelectionMark
                          active={
                            selected
                          }
                        />
                      </div>

                      <p className="mt-3 text-sm leading-6 text-text-secondary">
                        {item.description}
                      </p>
                    </button>
                  );
                },
              )}
            </div>
          </ServiceSection>

          {/* DESCRIPTION */}

          <ServiceSection
            eyebrow="Section 03"
            title="Service description"
            description="Explain what referred citizens can realistically expect from your organisation."
          >
            <label className="block">
              <span className="text-sm font-semibold text-text-primary">
                Describe your support
                services
              </span>

              <textarea
                rows={6}
                value={
                  form.serviceDescription
                }
                onChange={(event) => {
                  setForm(
                    (current) => ({
                      ...current,
                      serviceDescription:
                        event.target.value,
                    }),
                  );

                  setSaved(false);
                }}
                placeholder="Describe the services your organisation provides, who is eligible, any important limitations and what a referred citizen should expect."
                className="mt-3 w-full resize-y border border-border bg-background px-4 py-3 text-sm leading-6 text-text-primary outline-none transition focus:border-gold"
              />
            </label>
          </ServiceSection>

          {/* LANGUAGES */}

          <ServiceSection
            eyebrow="Section 04"
            title="Languages supported"
            description="Select the languages in which your team can comfortably provide support."
          >
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {languageOptions.map(
                (language) => (
                  <SelectionButton
                    key={language}
                    label={language}
                    active={
                      form.languages.includes(
                        language,
                      )
                    }
                    onClick={() =>
                      toggleArrayValue(
                        "languages",
                        language,
                      )
                    }
                  />
                ),
              )}
            </div>
          </ServiceSection>

          {/* CHANNELS */}

          <ServiceSection
            eyebrow="Section 05"
            title="Support channels"
            description="How can referred citizens receive support from your organisation?"
          >
            <div className="grid gap-4 md:grid-cols-3">
              {supportChannelOptions.map(
                (channel) => {
                  const selected =
                    form.supportChannels.includes(
                      channel.value,
                    );

                  return (
                    <button
                      key={channel.value}
                      type="button"
                      onClick={() =>
                        toggleArrayValue(
                          "supportChannels",
                          channel.value,
                        )
                      }
                      className={[
                        "min-h-[150px] border p-5 text-left transition",
                        selected
                          ? "border-gold bg-gold/5"
                          : "border-border bg-background hover:border-gold/60",
                      ].join(" ")}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <h3 className="font-semibold text-text-primary">
                          {channel.label}
                        </h3>

                        <SelectionMark
                          active={
                            selected
                          }
                        />
                      </div>

                      <p className="mt-3 text-sm leading-6 text-text-secondary">
                        {
                          channel.description
                        }
                      </p>
                    </button>
                  );
                },
              )}
            </div>
          </ServiceSection>

          {/* GEOGRAPHY */}

          <ServiceSection
            eyebrow="Section 06"
            title="Service coverage"
            description="Specify where your organisation can genuinely serve referred citizens."
          >
            <label className="flex items-start gap-3 border border-border bg-background p-4">
              <input
                type="checkbox"
                checked={
                  form.nationwide
                }
                onChange={(event) => {
                  setForm(
                    (current) => ({
                      ...current,
                      nationwide:
                        event.target.checked,
                    }),
                  );

                  setSaved(false);
                }}
                className="mt-1 h-4 w-4 accent-[#c99522]"
              />

              <div>
                <p className="font-semibold text-text-primary">
                  Nationwide coverage
                </p>

                <p className="mt-1 text-sm leading-6 text-text-secondary">
                  Select this only if
                  your organisation can
                  realistically support
                  citizens across
                  Uganda.
                </p>
              </div>
            </label>

            {!form.nationwide && (
              <div className="mt-6">
                <p className="text-sm font-semibold text-text-primary">
                  Districts served
                </p>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {districtOptions.map(
                    (district) => (
                      <SelectionButton
                        key={district}
                        label={district}
                        active={
                          form.districtsServed.includes(
                            district,
                          )
                        }
                        onClick={() =>
                          toggleArrayValue(
                            "districtsServed",
                            district,
                          )
                        }
                      />
                    ),
                  )}
                </div>
              </div>
            )}
          </ServiceSection>

          {/* CAPACITY */}

          <ServiceSection
            eyebrow="Section 07"
            title="Access & referral capacity"
            description="Set expectations about cost, appointments and whether your organisation is currently able to receive referrals."
          >
            <div className="grid gap-4 lg:grid-cols-3">
              <BooleanCard
                title="Free services available"
                description="At least some referred citizens can receive support without paying a service fee."
                checked={
                  form.freeServices
                }
                onChange={(
                  checked,
                ) => {
                  setForm(
                    (current) => ({
                      ...current,
                      freeServices:
                        checked,
                    }),
                  );

                  setSaved(false);
                }}
              />

              <BooleanCard
                title="Appointment required"
                description="Citizens should arrange an appointment before attending or receiving support."
                checked={
                  form.appointmentRequired
                }
                onChange={(
                  checked,
                ) => {
                  setForm(
                    (current) => ({
                      ...current,
                      appointmentRequired:
                        checked,
                    }),
                  );

                  setSaved(false);
                }}
              />

              <BooleanCard
                title="Accepting referrals"
                description="Your organisation currently has capacity to receive suitable referrals."
                checked={
                  form.acceptingReferrals
                }
                onChange={(
                  checked,
                ) => {
                  setForm(
                    (current) => ({
                      ...current,
                      acceptingReferrals:
                        checked,
                    }),
                  );

                  setSaved(false);
                }}
              />
            </div>

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <label>
                <span className="text-sm font-semibold text-text-primary">
                  Weekly referral limit
                </span>

                <input
                  type="number"
                  min="0"
                  value={
                    form.weeklyReferralLimit
                  }
                  onChange={(event) => {
                    setForm(
                      (current) => ({
                        ...current,
                        weeklyReferralLimit:
                          event.target.value,
                      }),
                    );

                    setSaved(false);
                  }}
                  placeholder="e.g. 10"
                  className="mt-2 min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none focus:border-gold"
                />
              </label>

              <label>
                <span className="text-sm font-semibold text-text-primary">
                  Availability note
                </span>

                <input
                  type="text"
                  value={
                    form.availabilityNote
                  }
                  onChange={(event) => {
                    setForm(
                      (current) => ({
                        ...current,
                        availabilityNote:
                          event.target.value,
                      }),
                    );

                    setSaved(false);
                  }}
                  placeholder="e.g. Monday–Friday, 8:30 AM–5:00 PM"
                  className="mt-2 min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none focus:border-gold"
                />
              </label>
            </div>

            <div className="mt-5 flex items-start gap-3 border-l-2 border-gold bg-gold/5 p-4">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <p className="text-xs leading-5 text-text-secondary">
                Turning on “Accepting
                referrals” does not make
                an organisation visible
                immediately. Verification
                is still required before
                referral matching is
                enabled.
              </p>
            </div>
          </ServiceSection>

          {/* SAVE */}

          <section className="sticky bottom-0 z-20 mt-6 border border-border bg-surface/95 p-4 shadow-[var(--shadow-soft)] backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {saving
                    ? "Saving services..."
                    : saved
                      ? "Service configuration saved"
                      : "Save your service configuration."}
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  Saved changes are
                  persisted through
                  Django and PostgreSQL.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={
                    handleSave
                  }
                  disabled={saving}
                  className="btn-secondary disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {saving ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : saved ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}

                  {saving
                    ? "Saving..."
                    : saved
                      ? "Saved"
                      : "Save Services"}
                </button>

                <Link
                  to="/partner/verification"
                  className="btn-primary"
                >
                  Continue to Verification

                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}

/* =========================================================
   COMPONENTS
========================================================= */

function ServiceSection({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="mt-6 border border-border bg-surface">
      <div className="border-b border-border p-6 sm:p-7">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
          {eyebrow}
        </p>

        <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
          {title}
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
          {description}
        </p>
      </div>

      <div className="p-6 sm:p-7">
        {children}
      </div>
    </section>
  );
}

function SelectionMark({
  active,
}: {
  active: boolean;
}) {
  return (
    <span
      className={[
        "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border",

        active
          ? "border-gold bg-gold text-[#191919]"
          : "border-border",
      ].join(" ")}
    >
      {active && (
        <Check className="h-3 w-3" />
      )}
    </span>
  );
}

function SelectionButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "flex min-h-12 items-center justify-between border px-4 text-left text-sm font-medium transition",

        active
          ? "border-gold bg-gold/5 text-text-primary"
          : "border-border bg-background text-text-secondary hover:border-gold/60 hover:text-text-primary",
      ].join(" ")}
    >
      {label}

      <SelectionMark
        active={active}
      />
    </button>
  );
}

function BooleanCard({
  title,
  description,
  checked,
  onChange,
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange:
    (checked: boolean) => void;
}) {
  return (
    <label
      className={[
        "flex min-h-[175px] cursor-pointer flex-col border p-5 transition",

        checked
          ? "border-gold bg-gold/5"
          : "border-border bg-background hover:border-gold/60",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-4">
        <p className="font-semibold text-text-primary">
          {title}
        </p>

        <input
          type="checkbox"
          checked={checked}
          onChange={(event) =>
            onChange(
              event.target.checked,
            )
          }
          className="mt-1 h-4 w-4 accent-[#c99522]"
        />
      </div>

      <p className="mt-3 text-sm leading-6 text-text-secondary">
        {description}
      </p>
    </label>
  );
}
