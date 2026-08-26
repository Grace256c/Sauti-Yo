import {
  ArrowRight,
  Check,
  Globe2,
  Languages,
  MapPin,
  Phone,
  Save,
  Scale,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { rightsCategories } from "../../data/rightsData";
import { supportPathways } from "../../data/supportData";

import type { CategorySlug } from "../../data/rightsData";
import type { SupportType } from "../../data/supportData";
import type { SupportChannel } from "../../data/partnerData";

type ServicesForm = {
  categories: CategorySlug[];
  supportTypes: SupportType[];
  languages: string[];
  supportChannels: SupportChannel[];
  districtsServed: string[];
  nationwide: boolean;
  freeServices: boolean;
  appointmentRequired: boolean;
  serviceDescription: string;
  acceptingReferrals: boolean;
};

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

const supportChannels: {
  id: SupportChannel;
  title: string;
  description: string;
  icon: typeof Phone;
}[] = [
  {
    id: "in-person",
    title: "In person",
    description:
      "Citizens can visit your organisation or service location.",
    icon: MapPin,
  },
  {
    id: "phone",
    title: "Phone",
    description:
      "Your organisation can provide support by telephone.",
    icon: Phone,
  },
  {
    id: "remote",
    title: "Online / remote",
    description:
      "Support can be provided remotely without requiring travel.",
    icon: Globe2,
  },
];

const initialForm: ServicesForm = {
  categories: [],
  supportTypes: [],
  languages: [],
  supportChannels: [],
  districtsServed: [],
  nationwide: false,
  freeServices: false,
  appointmentRequired: false,
  serviceDescription: "",
  acceptingReferrals: false,
};

export default function PartnerServices() {
  const [form, setForm] =
    useState<ServicesForm>(() => {
      try {
        const stored =
          sessionStorage.getItem(
            "sauti-yo-partner-services-draft",
          );

        return stored
          ? (JSON.parse(stored) as ServicesForm)
          : initialForm;
      } catch {
        return initialForm;
      }
    });

  const [saved, setSaved] =
    useState(false);

  const completion = useMemo(() => {
    const checks = [
      form.categories.length > 0,
      form.supportTypes.length > 0,
      form.languages.length > 0,
      form.supportChannels.length > 0,
      form.nationwide ||
        form.districtsServed.length > 0,
      form.serviceDescription.trim() !== "",
    ];

    const completed =
      checks.filter(Boolean).length;

    return Math.round(
      (completed / checks.length) * 100,
    );
  }, [form]);

  const toggleCategory = (
    slug: CategorySlug,
  ) => {
    setForm((current) => ({
      ...current,
      categories:
        current.categories.includes(slug)
          ? current.categories.filter(
              (item) => item !== slug,
            )
          : [...current.categories, slug],
    }));

    setSaved(false);
  };

  const toggleSupportType = (
    type: SupportType,
  ) => {
    setForm((current) => ({
      ...current,
      supportTypes:
        current.supportTypes.includes(type)
          ? current.supportTypes.filter(
              (item) => item !== type,
            )
          : [...current.supportTypes, type],
    }));

    setSaved(false);
  };

  const toggleLanguage = (
    language: string,
  ) => {
    setForm((current) => ({
      ...current,
      languages:
        current.languages.includes(language)
          ? current.languages.filter(
              (item) =>
                item !== language,
            )
          : [
              ...current.languages,
              language,
            ],
    }));

    setSaved(false);
  };

  const toggleChannel = (
    channel: SupportChannel,
  ) => {
    setForm((current) => ({
      ...current,
      supportChannels:
        current.supportChannels.includes(
          channel,
        )
          ? current.supportChannels.filter(
              (item) =>
                item !== channel,
            )
          : [
              ...current.supportChannels,
              channel,
            ],
    }));

    setSaved(false);
  };

  const toggleDistrict = (
    district: string,
  ) => {
    setForm((current) => ({
      ...current,
      districtsServed:
        current.districtsServed.includes(
          district,
        )
          ? current.districtsServed.filter(
              (item) =>
                item !== district,
            )
          : [
              ...current.districtsServed,
              district,
            ],
    }));

    setSaved(false);
  };

  const handleSave = () => {
    sessionStorage.setItem(
      "sauti-yo-partner-services-draft",
      JSON.stringify(form),
    );

    setSaved(true);

    window.setTimeout(() => {
      setSaved(false);
    }, 3000);
  };

  return (
    <>
      {/* PAGE HEADER */}
      <section className="border-b border-border bg-surface">
        <div className="px-5 py-8 sm:px-8 lg:px-10 lg:py-9 xl:px-12">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Service configuration
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Services
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Tell Sauti Yo which rights issues your organisation
                handles, where you operate and how citizens can receive
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
                  className="h-full bg-gold transition-all duration-300"
                  style={{
                    width: `${completion}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">
          {/* INTRO */}
          <section className="border border-border bg-surface p-5 sm:p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                <Scale
                  className="h-5 w-5"
                  strokeWidth={1.7}
                />
              </div>

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Referral matching
                </p>

                <h2 className="mt-2 text-lg font-semibold text-text-primary">
                  Accurate service information improves matching.
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                  These selections will eventually help Sauti Yo
                  determine whether your organisation is an appropriate
                  match for a citizen's issue, location, language and
                  preferred support method.
                </p>
              </div>
            </div>
          </section>

          {/* RIGHTS CATEGORIES */}
          <ServiceSection
            eyebrow="Section 01"
            title="Rights issues handled"
            description="Select the citizen-facing rights categories your organisation is genuinely equipped to support."
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {rightsCategories.map(
                (category) => {
                  const Icon =
                    category.icon;

                  const active =
                    form.categories.includes(
                      category.slug,
                    );

                  return (
                    <button
                      key={category.slug}
                      type="button"
                      onClick={() =>
                        toggleCategory(
                          category.slug,
                        )
                      }
                      className={[
                        "group flex min-h-[190px] flex-col items-start border p-5 text-left transition",

                        active
                          ? "border-gold bg-gold/5"
                          : "border-border bg-background hover:border-gold/60",
                      ].join(" ")}
                    >
                      <div className="flex w-full items-start justify-between gap-4">
                        <div
                          className={[
                            "flex h-10 w-10 items-center justify-center rounded-full",

                            active
                              ? "bg-gold text-[#191919]"
                              : "bg-gold/10 text-gold",
                          ].join(" ")}
                        >
                          <Icon
                            className="h-5 w-5"
                            strokeWidth={1.7}
                          />
                        </div>

                        <SelectionMark
                          active={active}
                        />
                      </div>

                      <h3 className="mt-5 font-semibold text-text-primary">
                        {category.title}
                      </h3>

                      <p className="mt-2 text-sm leading-6 text-text-secondary">
                        {
                          category.shortDescription
                        }
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
              {supportPathways.map(
                (pathway) => {
                  const Icon =
                    pathway.icon;

                  const active =
                    form.supportTypes.includes(
                      pathway.id,
                    );

                  return (
                    <button
                      key={pathway.id}
                      type="button"
                      onClick={() =>
                        toggleSupportType(
                          pathway.id,
                        )
                      }
                      className={[
                        "flex min-h-[180px] items-start gap-4 border p-5 text-left transition",

                        active
                          ? "border-gold bg-gold/5"
                          : "border-border bg-background hover:border-gold/60",
                      ].join(" ")}
                    >
                      <div
                        className={[
                          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",

                          active
                            ? "bg-gold text-[#191919]"
                            : "bg-gold/10 text-gold",
                        ].join(" ")}
                      >
                        <Icon
                          className="h-5 w-5"
                          strokeWidth={1.7}
                        />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-start justify-between gap-4">
                          <h3 className="font-semibold text-text-primary">
                            {pathway.title}
                          </h3>

                          <SelectionMark
                            active={active}
                          />
                        </div>

                        <p className="mt-2 text-sm leading-6 text-text-secondary">
                          {
                            pathway.description
                          }
                        </p>
                      </div>
                    </button>
                  );
                },
              )}
            </div>
          </ServiceSection>

          {/* SERVICE DESCRIPTION */}
          <ServiceSection
            eyebrow="Section 03"
            title="Service description"
            description="Explain what referred citizens can realistically expect from your organisation."
          >
            <label
              htmlFor="service-description"
              className="block text-sm font-semibold text-text-primary"
            >
              Describe your support services
              <span className="ml-1 text-gold">
                *
              </span>
            </label>

            <textarea
              id="service-description"
              value={
                form.serviceDescription
              }
              onChange={(event) => {
                setForm((current) => ({
                  ...current,
                  serviceDescription:
                    event.target.value,
                }));

                setSaved(false);
              }}
              rows={6}
              placeholder="Describe the services your organisation provides, who is eligible, any important limitations and what a referred citizen should expect."
              className="mt-2 w-full resize-y border border-border bg-background px-4 py-3 text-sm leading-6 text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
            />

            <p className="mt-2 text-xs leading-5 text-text-secondary">
              Avoid broad claims such as
              “we handle everything”.
              Accurate descriptions help
              prevent unsuitable
              referrals.
            </p>
          </ServiceSection>

          {/* LANGUAGES */}
          <ServiceSection
            eyebrow="Section 04"
            title="Languages supported"
            description="Select the languages in which your team can comfortably provide support."
          >
            <div className="mb-5 flex items-start gap-3">
              <Languages className="mt-0.5 h-5 w-5 text-gold" />

              <p className="text-sm leading-6 text-text-secondary">
                Only select languages
                that can realistically
                be supported during a
                citizen referral.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {languageOptions.map(
                (language) => {
                  const active =
                    form.languages.includes(
                      language,
                    );

                  return (
                    <SelectionButton
                      key={language}
                      label={language}
                      active={active}
                      onClick={() =>
                        toggleLanguage(
                          language,
                        )
                      }
                    />
                  );
                },
              )}
            </div>
          </ServiceSection>

          {/* SUPPORT CHANNELS */}
          <ServiceSection
            eyebrow="Section 05"
            title="How support is delivered"
            description="Select all channels your organisation can use for citizen support."
          >
            <div className="grid gap-4 md:grid-cols-3">
              {supportChannels.map(
                (channel) => {
                  const Icon =
                    channel.icon;

                  const active =
                    form.supportChannels.includes(
                      channel.id,
                    );

                  return (
                    <button
                      key={channel.id}
                      type="button"
                      onClick={() =>
                        toggleChannel(
                          channel.id,
                        )
                      }
                      className={[
                        "flex min-h-[190px] flex-col items-start border p-5 text-left transition",

                        active
                          ? "border-gold bg-gold/5"
                          : "border-border bg-background hover:border-gold/60",
                      ].join(" ")}
                    >
                      <div className="flex w-full items-start justify-between">
                        <div
                          className={[
                            "flex h-10 w-10 items-center justify-center rounded-full",

                            active
                              ? "bg-gold text-[#191919]"
                              : "bg-gold/10 text-gold",
                          ].join(" ")}
                        >
                          <Icon className="h-5 w-5" />
                        </div>

                        <SelectionMark
                          active={active}
                        />
                      </div>

                      <h3 className="mt-4 font-semibold text-text-primary">
                        {channel.title}
                      </h3>

                      <p className="mt-2 text-sm leading-6 text-text-secondary">
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
                checked={form.nationwide}
                onChange={(event) => {
                  setForm((current) => ({
                    ...current,
                    nationwide:
                      event.target.checked,
                  }));

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
                        active={form.districtsServed.includes(
                          district,
                        )}
                        onClick={() =>
                          toggleDistrict(
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

          {/* ACCESS + CAPACITY */}
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
                onChange={(checked) => {
                  setForm((current) => ({
                    ...current,
                    freeServices:
                      checked,
                  }));

                  setSaved(false);
                }}
              />

              <BooleanCard
                title="Appointment required"
                description="Citizens should arrange an appointment before attending or receiving support."
                checked={
                  form.appointmentRequired
                }
                onChange={(checked) => {
                  setForm((current) => ({
                    ...current,
                    appointmentRequired:
                      checked,
                  }));

                  setSaved(false);
                }}
              />

              <BooleanCard
                title="Accepting referrals"
                description="Your organisation currently has capacity to receive suitable referrals."
                checked={
                  form.acceptingReferrals
                }
                onChange={(checked) => {
                  setForm((current) => ({
                    ...current,
                    acceptingReferrals:
                      checked,
                  }));

                  setSaved(false);
                }}
              />
            </div>

            <div className="mt-5 flex items-start gap-3 border-l-2 border-gold bg-gold/5 p-4">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <p className="text-xs leading-5 text-text-secondary">
                Turning on “Accepting
                referrals” does not make
                the organisation visible
                immediately. The partner
                must still be verified
                and eligible for
                matching.
              </p>
            </div>
          </ServiceSection>

          {/* SAVE BAR */}
          <section className="sticky bottom-0 z-20 mt-6 border border-border bg-surface/95 p-4 shadow-[var(--shadow-soft)] backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {saved
                    ? "Service draft saved"
                    : "Save your service configuration."}
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  This prototype stores
                  the draft in the
                  current browser
                  session.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={handleSave}
                  className="btn-secondary"
                >
                  {saved ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}

                  {saved
                    ? "Saved"
                    : "Save Draft"}
                </button>

                <Link
                  to="/partner/referrals"
                  className="btn-primary"
                >
                  Continue
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

function ServiceSection({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
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

      <SelectionMark active={active} />
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
  onChange: (checked: boolean) => void;
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