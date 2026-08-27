import {
  AlertCircle,
  ArrowRight,
  Building2,
  Check,
  FileText,
  Globe2,
  LoaderCircle,
  MapPin,
  Phone,
  Save,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";

import {
  usePartnerAuth,
} from "../../context/PartnerAuthContext";

import { ApiError } from "../../services/api";

import {
  getPartnerOrganisation,
  updatePartnerOrganisation,
  updatePartnerServices,
  type PartnerOrganisation,
} from "../../services/partners";

/* =========================================================
   TYPES
========================================================= */

type OrganisationType =
  | ""
  | "legal_aid"
  | "ngo"
  | "cbo"
  | "government"
  | "law_firm"
  | "protection_service"
  | "mediation_service"
  | "other";

type ProfileForm = {
  organisationName: string;
  organisationType: OrganisationType;

  registrationNumber: string;
  yearEstablished: string;

  description: string;

  headquartersDistrict: string;
  physicalAddress: string;

  areasServed: string[];

  website: string;
  publicEmail: string;
  publicPhone: string;
};

/* =========================================================
   OPTIONS
========================================================= */

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

const organisationTypes: {
  value: OrganisationType;
  label: string;
}[] = [
  {
    value: "",
    label: "Select organisation type",
  },
  {
    value: "legal_aid",
    label: "Legal aid organisation",
  },
  {
    value: "ngo",
    label: "Non-governmental organisation (NGO)",
  },
  {
    value: "cbo",
    label: "Community-based organisation (CBO)",
  },
  {
    value: "government",
    label: "Government institution",
  },
  {
    value: "law_firm",
    label: "Law firm",
  },
  {
    value: "protection_service",
    label: "Protection / safeguarding service",
  },
  {
    value: "mediation_service",
    label: "Mediation / dispute-resolution service",
  },
  {
    value: "other",
    label: "Other organisation",
  },
];

const initialForm: ProfileForm = {
  organisationName: "",
  organisationType: "",
  registrationNumber: "",
  yearEstablished: "",
  description: "",
  headquartersDistrict: "",
  physicalAddress: "",
  areasServed: [],
  website: "",
  publicEmail: "",
  publicPhone: "",
};

/* =========================================================
   DATA MAPPING
========================================================= */

function organisationToForm(
  organisation: PartnerOrganisation,
): ProfileForm {
  return {
    organisationName:
      organisation.support_service.name ?? "",

    organisationType:
      organisation.organisation_type as OrganisationType,

    registrationNumber:
      organisation.registration_number ?? "",

    yearEstablished:
      organisation.year_established !== null &&
      organisation.year_established !== undefined
        ? String(organisation.year_established)
        : "",

    description:
      organisation.support_service.description ?? "",

    headquartersDistrict:
      organisation.headquarters_district ?? "",

    physicalAddress:
      organisation.physical_address ?? "",

    areasServed:
      organisation.service_configuration?.districts_served ??
      [],

    website:
      organisation.support_service.website ?? "",

    publicEmail:
      organisation.public_email ?? "",

    publicPhone:
      organisation.public_phone ?? "",
  };
}

/* =========================================================
   PAGE
========================================================= */

export default function PartnerProfile() {
  const { session } = usePartnerAuth();

  const [form, setForm] =
    useState<ProfileForm>(initialForm);

  const [organisation, setOrganisation] =
    useState<PartnerOrganisation | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [saved, setSaved] =
    useState(false);

  const [error, setError] =
    useState("");

  const organisationId =
    session?.membership.organisation_id;

  /* =======================================================
     LOAD PROFILE
  ======================================================= */

  useEffect(() => {
    if (!organisationId) {
      setLoading(false);
      return;
    }

    const activeOrganisationId =
      organisationId;

    let active = true;

    async function loadProfile() {
      setLoading(true);
      setError("");

      try {
        const data =
          await getPartnerOrganisation(
            activeOrganisationId,
          );

        if (!active) {
          return;
        }

        setOrganisation(data);

        setForm(
          organisationToForm(
            data,
          ),
        );
      } catch (caughtError) {
        if (!active) {
          return;
        }

        if (
          caughtError instanceof ApiError
        ) {
          setError(
            caughtError.message,
          );
        } else {
          setError(
            "Unable to load the organisation profile.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, [organisationId]);

  /* =======================================================
     PROFILE COMPLETION
  ======================================================= */

  const completion = useMemo(() => {
    const requiredValues = [
      form.organisationName,
      form.organisationType,
      form.description,
      form.headquartersDistrict,
      form.physicalAddress,
    ];

    const completed =
      requiredValues.filter(
        (value) =>
          String(value).trim() !== "",
      ).length;

    return Math.round(
      (completed /
        requiredValues.length) *
        100,
    );
  }, [form]);

  /* =======================================================
     FORM HELPERS
  ======================================================= */

  function updateField<
    K extends keyof ProfileForm,
  >(
    field: K,
    value: ProfileForm[K],
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setSaved(false);
  }

  function toggleDistrict(
    district: string,
  ) {
    setForm((current) => {
      const selected =
        current.areasServed.includes(
          district,
        );

      return {
        ...current,

        areasServed: selected
          ? current.areasServed.filter(
              (item) =>
                item !== district,
            )
          : [
              ...current.areasServed,
              district,
            ],
      };
    });

    setSaved(false);
  }

  /* =======================================================
     SAVE PROFILE
  ======================================================= */

  async function handleSave() {
    if (!organisationId) {
      setError(
        "No partner organisation is connected to this account.",
      );
      return;
    }

    setSaving(true);
    setSaved(false);
    setError("");

    try {
      let yearEstablished:
        | number
        | null = null;

      if (
        form.yearEstablished.trim()
      ) {
        const parsedYear =
          Number(
            form.yearEstablished,
          );

        if (
          !Number.isInteger(
            parsedYear,
          ) ||
          parsedYear < 0
        ) {
          setError(
            "Please enter a valid year established.",
          );

          setSaving(false);
          return;
        }

        yearEstablished =
          parsedYear;
      }

      const updatedOrganisation =
        await updatePartnerOrganisation(
          organisationId,
          {
            support_service: {
              name:
                form.organisationName.trim(),

              description:
                form.description.trim(),

              website:
                form.website.trim(),
            },

            organisation_type:
              form.organisationType,

            registration_number:
              form.registrationNumber.trim(),

            year_established:
              yearEstablished,

            headquarters_district:
              form.headquartersDistrict,

            physical_address:
              form.physicalAddress.trim(),

            public_email:
              form.publicEmail.trim(),

            public_phone:
              form.publicPhone.trim(),
          },
        );

      const updatedServices =
        await updatePartnerServices(
          organisationId,
          {
            districts_served:
              form.areasServed,
          },
        );

      const combinedOrganisation:
        PartnerOrganisation = {
        ...updatedOrganisation,

        service_configuration:
          updatedServices,
      };

      setOrganisation(
        combinedOrganisation,
      );

      setForm(
        organisationToForm(
          combinedOrganisation,
        ),
      );

      setSaved(true);

      window.setTimeout(() => {
        setSaved(false);
      }, 3000);
    } catch (caughtError) {
      if (
        caughtError instanceof ApiError
      ) {
        setError(
          caughtError.message,
        );
      } else {
        setError(
          "Unable to save the organisation profile.",
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
            Loading organisation
            profile...
          </p>
        </div>
      </div>
    );
  }

  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <>
      {/* HEADER */}

      <section className="border-b border-border bg-surface">
        <div className="px-5 py-8 sm:px-8 lg:px-10 lg:py-9 xl:px-12">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Organisation
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Organisation Profile
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Manage your organisation
                information, location and
                public contact details.
              </p>
            </div>

            <div className="min-w-[220px]">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-text-secondary">
                  Profile completion
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

      {/* CONTENT */}

      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">

          {/* ERROR */}

          {error && (
            <div className="mb-6 flex items-start gap-3 border border-danger/30 bg-danger/5 p-4">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />

              <p className="text-sm leading-6 text-danger">
                {error}
              </p>
            </div>
          )}

          {/* STATUS */}

          <section className="border border-border bg-surface p-5 sm:p-6">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                <ShieldCheck
                  className="h-5 w-5"
                  strokeWidth={1.7}
                />
              </div>

              <div className="flex-1">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Organisation setup
                </p>

                <h2 className="mt-2 text-lg font-semibold text-text-primary">
                  Complete your partner
                  profile.
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                  Your organisation
                  information is securely
                  stored through the
                  Sauti Yo partner
                  platform.
                </p>
              </div>
            </div>
          </section>

          {/* ORGANISATION DETAILS */}

          <FormSection
            icon={Building2}
            eyebrow="Section 01"
            title="Organisation details"
            description="Basic information that identifies your organisation."
          >
            <div className="grid gap-5 md:grid-cols-2">
              <Field>
                <Label
                  htmlFor="organisation-name"
                  required
                >
                  Organisation name
                </Label>

                <Input
                  id="organisation-name"
                  value={
                    form.organisationName
                  }
                  onChange={(value) =>
                    updateField(
                      "organisationName",
                      value,
                    )
                  }
                  placeholder="e.g. Justice Access Centre"
                />
              </Field>

              <Field>
                <Label
                  htmlFor="organisation-type"
                  required
                >
                  Organisation type
                </Label>

                <select
                  id="organisation-type"
                  value={
                    form.organisationType
                  }
                  onChange={(event) =>
                    updateField(
                      "organisationType",
                      event.target
                        .value as OrganisationType,
                    )
                  }
                  className="min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                >
                  {organisationTypes.map(
                    (type) => (
                      <option
                        key={type.value}
                        value={type.value}
                      >
                        {type.label}
                      </option>
                    ),
                  )}
                </select>
              </Field>

              <Field>
                <Label htmlFor="registration-number">
                  Registration number
                </Label>

                <Input
                  id="registration-number"
                  value={
                    form.registrationNumber
                  }
                  onChange={(value) =>
                    updateField(
                      "registrationNumber",
                      value,
                    )
                  }
                  placeholder="Organisation registration number"
                />
              </Field>

              <Field>
                <Label htmlFor="year-established">
                  Year established
                </Label>

                <Input
                  id="year-established"
                  value={
                    form.yearEstablished
                  }
                  onChange={(value) =>
                    updateField(
                      "yearEstablished",
                      value,
                    )
                  }
                  placeholder="e.g. 2018"
                  type="number"
                />
              </Field>

              <div className="md:col-span-2">
                <Field>
                  <Label
                    htmlFor="organisation-description"
                    required
                  >
                    Organisation
                    description
                  </Label>

                  <textarea
                    id="organisation-description"
                    value={
                      form.description
                    }
                    onChange={(event) =>
                      updateField(
                        "description",
                        event.target.value,
                      )
                    }
                    rows={5}
                    placeholder="Briefly describe your organisation, who you serve and the type of work you do."
                    className="w-full resize-y border border-border bg-background px-4 py-3 text-sm leading-6 text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
                  />

                  <HelperText>
                    Give citizens and the
                    Sauti Yo team a clear
                    understanding of the
                    support your
                    organisation provides.
                  </HelperText>
                </Field>
              </div>
            </div>
          </FormSection>

          {/* ACCOUNT CONTACT */}

          <FormSection
            icon={UserRound}
            eyebrow="Section 02"
            title="Account contact"
            description="The authenticated partner member currently managing this workspace."
          >
            <div className="grid gap-5 md:grid-cols-2">
              <ReadOnlyField
                label="Name"
                value={
                  [
                    session?.user
                      .first_name,
                    session?.user
                      .last_name,
                  ]
                    .filter(Boolean)
                    .join(" ") ||
                  session?.user
                    .username ||
                  "—"
                }
              />

              <ReadOnlyField
                label="Role"
                value={formatRole(
                  session?.membership
                    .role,
                )}
              />

              <ReadOnlyField
                label="Account email"
                value={
                  session?.user.email ||
                  "Not provided"
                }
              />

              <ReadOnlyField
                label="Username"
                value={
                  session?.user
                    .username ||
                  "—"
                }
              />
            </div>

            <div className="mt-5 flex items-start gap-3 border-l-2 border-gold bg-gold/5 p-4">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <p className="text-xs leading-5 text-text-secondary">
                These details belong to
                the authenticated partner
                account and are kept
                separate from the
                organisation's public
                contact information.
              </p>
            </div>
          </FormSection>

          {/* LOCATION */}

          <FormSection
            icon={MapPin}
            eyebrow="Section 03"
            title="Location & coverage"
            description="Tell us where your organisation is based and where it can provide support."
          >
            <div className="grid gap-5 md:grid-cols-2">
              <Field>
                <Label
                  htmlFor="headquarters-district"
                  required
                >
                  Headquarters district
                </Label>

                <select
                  id="headquarters-district"
                  value={
                    form.headquartersDistrict
                  }
                  onChange={(event) =>
                    updateField(
                      "headquartersDistrict",
                      event.target.value,
                    )
                  }
                  className="min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                >
                  <option value="">
                    Select district
                  </option>

                  {districtOptions.map(
                    (district) => (
                      <option
                        key={district}
                        value={district}
                      >
                        {district}
                      </option>
                    ),
                  )}
                </select>
              </Field>

              <Field>
                <Label
                  htmlFor="physical-address"
                  required
                >
                  Physical address
                </Label>

                <Input
                  id="physical-address"
                  value={
                    form.physicalAddress
                  }
                  onChange={(value) =>
                    updateField(
                      "physicalAddress",
                      value,
                    )
                  }
                  placeholder="Office location / address"
                />
              </Field>
            </div>

            <div className="mt-7">
              <p className="text-sm font-semibold text-text-primary">
                Districts served
              </p>

              <p className="mt-2 text-sm leading-6 text-text-secondary">
                Select the districts
                where your organisation
                can currently provide
                support.
              </p>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {districtOptions.map(
                  (district) => {
                    const selected =
                      form.areasServed.includes(
                        district,
                      );

                    return (
                      <button
                        key={district}
                        type="button"
                        onClick={() =>
                          toggleDistrict(
                            district,
                          )
                        }
                        className={[
                          "flex min-h-12 items-center justify-between border px-4 text-left text-sm font-medium transition",

                          selected
                            ? "border-gold bg-gold/5 text-text-primary"
                            : "border-border bg-background text-text-secondary hover:border-gold/60 hover:text-text-primary",
                        ].join(" ")}
                      >
                        <span>
                          {district}
                        </span>

                        <span
                          className={[
                            "flex h-5 w-5 items-center justify-center rounded-full border",

                            selected
                              ? "border-gold bg-gold text-[#191919]"
                              : "border-border",
                          ].join(" ")}
                        >
                          {selected && (
                            <Check className="h-3 w-3" />
                          )}
                        </span>
                      </button>
                    );
                  },
                )}
              </div>
            </div>
          </FormSection>

          {/* PUBLIC INFORMATION */}

          <FormSection
            icon={Globe2}
            eyebrow="Section 04"
            title="Public information"
            description="Contact information that may be used when citizens are connected to your organisation."
          >
            <div className="grid gap-5 md:grid-cols-2">
              <Field>
                <Label htmlFor="website">
                  Website
                </Label>

                <Input
                  id="website"
                  value={form.website}
                  onChange={(value) =>
                    updateField(
                      "website",
                      value,
                    )
                  }
                  placeholder="https://..."
                  type="url"
                />
              </Field>

              <Field>
                <Label htmlFor="public-email">
                  Public support email
                </Label>

                <Input
                  id="public-email"
                  value={
                    form.publicEmail
                  }
                  onChange={(value) =>
                    updateField(
                      "publicEmail",
                      value,
                    )
                  }
                  placeholder="support@organisation.org"
                  type="email"
                />
              </Field>

              <Field>
                <Label htmlFor="public-phone">
                  Public support phone
                </Label>

                <Input
                  id="public-phone"
                  value={
                    form.publicPhone
                  }
                  onChange={(value) =>
                    updateField(
                      "publicPhone",
                      value,
                    )
                  }
                  placeholder="+256 ..."
                  type="tel"
                />
              </Field>
            </div>

            <div className="mt-5 flex items-start gap-3 border border-border bg-background p-4">
              <Phone className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <p className="text-xs leading-5 text-text-secondary">
                Only provide contact
                information your
                organisation is
                comfortable using for
                citizen support and
                referrals.
              </p>
            </div>
          </FormSection>

          {/* VERIFICATION */}

          <FormSection
            icon={FileText}
            eyebrow="Section 05"
            title="Verification preparation"
            description="Supporting evidence helps Sauti Yo verify organisations before referrals are enabled."
          >
            <div className="grid gap-4 md:grid-cols-2">
              <VerificationItem
                title="Registration evidence"
                description="Certificate, registration document or other formal evidence of the organisation."
              />

              <VerificationItem
                title="Organisation identification"
                description="Documents or information that help confirm the organisation's identity and operating status."
              />
            </div>

            <div className="mt-5 border-l-2 border-gold bg-gold/5 p-4">
              <p className="text-sm font-semibold text-text-primary">
                Verification is handled
                separately.
              </p>

              <p className="mt-2 text-xs leading-5 text-text-secondary">
                Complete your profile and
                service information
                before submitting your
                organisation for
                verification.
              </p>
            </div>
          </FormSection>

          {/* SAVE */}

          <section className="sticky bottom-0 z-20 mt-6 border border-border bg-surface/95 p-4 shadow-[var(--shadow-soft)] backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {saving
                    ? "Saving profile..."
                    : saved
                      ? "Profile saved successfully"
                      : "Save your changes before continuing."}
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  Saved changes remain
                  available when you
                  refresh or sign in
                  again.
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
                      : "Save Profile"}
                </button>

                <Link
                  to="/partner/services"
                  className="btn-primary"
                >
                  Continue to Services

                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </section>

          {!organisation && (
            <div className="mt-5 border border-border bg-surface p-4">
              <p className="text-xs text-text-secondary">
                No organisation profile
                data is currently
                available.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* =========================================================
   COMPONENTS
========================================================= */

function FormSection({
  icon: Icon,
  eyebrow,
  title,
  description,
  children,
}: {
  icon: typeof Building2;
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="mt-6 border border-border bg-surface">
      <div className="border-b border-border p-6 sm:p-7">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
            <Icon
              className="h-5 w-5"
              strokeWidth={1.7}
            />
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
              {eyebrow}
            </p>

            <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
              {title}
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
              {description}
            </p>
          </div>
        </div>
      </div>

      <div className="p-6 sm:p-7">
        {children}
      </div>
    </section>
  );
}

function Field({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      {children}
    </div>
  );
}

function Label({
  htmlFor,
  required = false,
  children,
}: {
  htmlFor: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="block text-sm font-semibold text-text-primary"
    >
      {children}

      {required && (
        <span className="ml-1 text-gold">
          *
        </span>
      )}
    </label>
  );
}

function Input({
  id,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  id: string;
  value: string;
  onChange: (
    value: string,
  ) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      onChange={(event) =>
        onChange(
          event.target.value,
        )
      }
      placeholder={placeholder}
      className="min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
    />
  );
}

function HelperText({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <p className="text-xs leading-5 text-text-secondary">
      {children}
    </p>
  );
}

function ReadOnlyField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-sm font-semibold text-text-primary">
        {label}
      </p>

      <div className="mt-2 flex min-h-12 items-center border border-border bg-background px-4">
        <p className="text-sm text-text-secondary">
          {value}
        </p>
      </div>
    </div>
  );
}

function VerificationItem({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="border border-border bg-background p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <FileText
            className="h-4 w-4"
            strokeWidth={1.7}
          />
        </div>

        <div>
          <h3 className="font-semibold text-text-primary">
            {title}
          </h3>

          <p className="mt-2 text-xs leading-5 text-text-secondary">
            {description}
          </p>

          <span className="mt-4 inline-flex border border-border px-3 py-1.5 text-[11px] font-semibold text-text-secondary">
            Verification document
          </span>
        </div>
      </div>
    </div>
  );
}

function formatRole(
  role?: string,
) {
  if (!role) {
    return "—";
  }

  return role
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}