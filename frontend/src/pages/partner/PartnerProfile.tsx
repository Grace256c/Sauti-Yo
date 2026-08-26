import {
  ArrowRight,
  Building2,
  Check,
  FileText,
  Globe2,
  MapPin,
  Phone,
  Save,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

type OrganisationType =
  | ""
  | "legal-aid"
  | "ngo"
  | "cbo"
  | "government"
  | "law-firm"
  | "protection-service"
  | "mediation-service"
  | "other";

type ProfileForm = {
  organisationName: string;
  organisationType: OrganisationType;
  registrationNumber: string;
  yearEstablished: string;
  description: string;

  contactName: string;
  contactRole: string;
  contactEmail: string;
  contactPhone: string;

  headquartersDistrict: string;
  physicalAddress: string;
  areasServed: string[];

  website: string;
  publicEmail: string;
  publicPhone: string;
};

const PROFILE_STORAGE_KEY =
  "sauti-yo-partner-profile-draft";

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
    value: "legal-aid",
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
    value: "law-firm",
    label: "Law firm",
  },
  {
    value: "protection-service",
    label: "Protection / safeguarding service",
  },
  {
    value: "mediation-service",
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

  contactName: "",
  contactRole: "",
  contactEmail: "",
  contactPhone: "",

  headquartersDistrict: "",
  physicalAddress: "",
  areasServed: [],

  website: "",
  publicEmail: "",
  publicPhone: "",
};

function loadSavedProfile(): ProfileForm {
  try {
    const stored =
      sessionStorage.getItem(
        PROFILE_STORAGE_KEY,
      );

    if (!stored) {
      return initialForm;
    }

    const parsed =
      JSON.parse(stored) as Partial<ProfileForm>;

    return {
      ...initialForm,
      ...parsed,

      areasServed:
        Array.isArray(parsed.areasServed)
          ? parsed.areasServed
          : [],
    };
  } catch {
    return initialForm;
  }
}

export default function PartnerProfile() {
  const [form, setForm] =
    useState<ProfileForm>(
      loadSavedProfile,
    );

  const [saved, setSaved] =
    useState(false);

  const requiredFields = useMemo(
    () => [
      form.organisationName,
      form.organisationType,
      form.description,
      form.contactName,
      form.contactRole,
      form.contactEmail,
      form.contactPhone,
      form.headquartersDistrict,
      form.physicalAddress,
    ],
    [form],
  );

  const completion = useMemo(() => {
    const complete =
      requiredFields.filter(
        (value) =>
          String(value).trim() !== "",
      ).length;

    return Math.round(
      (complete /
        requiredFields.length) *
        100,
    );
  }, [requiredFields]);

  const updateField = <
    K extends keyof ProfileForm,
  >(
    field: K,
    value: ProfileForm[K],
  ) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setSaved(false);
  };

  const toggleDistrict = (
    district: string,
  ) => {
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
  };

  const handleSave = () => {
    sessionStorage.setItem(
      PROFILE_STORAGE_KEY,
      JSON.stringify(form),
    );

    setSaved(true);

    window.setTimeout(() => {
      setSaved(false);
    }, 3000);
  };

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
                Organisation
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Organisation Profile
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Tell Sauti Yo who your
                organisation is, how to
                contact you and where
                you operate.
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

      {/* =====================================================
          PROFILE BODY
      ===================================================== */}
      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">
          {/* STATUS NOTE */}
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
                  Profile setup
                </p>

                <h2 className="mt-2 text-lg font-semibold text-text-primary">
                  Complete accurate
                  organisation information.
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                  This information will
                  support verification
                  and later help Sauti Yo
                  determine whether your
                  organisation is
                  suitable for citizen
                  referrals.
                </p>
              </div>
            </div>
          </section>

          {/* =================================================
              ORGANISATION DETAILS
          ================================================= */}
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
                    Organisation description
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
                    Keep this factual
                    and concise. Service
                    details will be
                    configured separately
                    on the Services page.
                  </HelperText>
                </Field>
              </div>
            </div>
          </FormSection>

          {/* =================================================
              PRIMARY CONTACT
          ================================================= */}
          <FormSection
            icon={UserRound}
            eyebrow="Section 02"
            title="Primary contact"
            description="The person Sauti Yo can contact about verification and referrals."
          >
            <div className="grid gap-5 md:grid-cols-2">
              <Field>
                <Label
                  htmlFor="contact-name"
                  required
                >
                  Full name
                </Label>

                <Input
                  id="contact-name"
                  value={
                    form.contactName
                  }
                  onChange={(value) =>
                    updateField(
                      "contactName",
                      value,
                    )
                  }
                  placeholder="Primary contact name"
                />
              </Field>

              <Field>
                <Label
                  htmlFor="contact-role"
                  required
                >
                  Role / title
                </Label>

                <Input
                  id="contact-role"
                  value={
                    form.contactRole
                  }
                  onChange={(value) =>
                    updateField(
                      "contactRole",
                      value,
                    )
                  }
                  placeholder="e.g. Programme Manager"
                />
              </Field>

              <Field>
                <Label
                  htmlFor="contact-email"
                  required
                >
                  Email address
                </Label>

                <Input
                  id="contact-email"
                  value={
                    form.contactEmail
                  }
                  onChange={(value) =>
                    updateField(
                      "contactEmail",
                      value,
                    )
                  }
                  placeholder="name@organisation.org"
                  type="email"
                />
              </Field>

              <Field>
                <Label
                  htmlFor="contact-phone"
                  required
                >
                  Phone / WhatsApp
                </Label>

                <Input
                  id="contact-phone"
                  value={
                    form.contactPhone
                  }
                  onChange={(value) =>
                    updateField(
                      "contactPhone",
                      value,
                    )
                  }
                  placeholder="+256 ..."
                  type="tel"
                />
              </Field>
            </div>

            <div className="mt-5 flex items-start gap-3 border-l-2 border-gold bg-gold/5 p-4">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <p className="text-xs leading-5 text-text-secondary">
                Primary contact details
                are for partner
                administration and
                should not automatically
                be displayed publicly to
                citizens.
              </p>
            </div>
          </FormSection>

          {/* =================================================
              LOCATION
          ================================================= */}
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
                Select all districts
                where your organisation
                can realistically
                provide support.
              </p>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {districtOptions.map(
                  (district) => {
                    const active =
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

                          active
                            ? "border-gold bg-gold/5 text-text-primary"
                            : "border-border bg-background text-text-secondary hover:border-gold/60 hover:text-text-primary",
                        ].join(" ")}
                      >
                        {district}

                        <span
                          className={[
                            "flex h-5 w-5 items-center justify-center rounded-full border",

                            active
                              ? "border-gold bg-gold text-[#191919]"
                              : "border-border",
                          ].join(" ")}
                        >
                          {active && (
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

          {/* =================================================
              PUBLIC CONTACT
          ================================================= */}
          <FormSection
            icon={Globe2}
            eyebrow="Section 04"
            title="Public information"
            description="Optional details that may later be shown to citizens when your organisation is an approved referral match."
          >
            <div className="grid gap-5 md:grid-cols-2">
              <Field>
                <Label htmlFor="website">
                  Website
                </Label>

                <Input
                  id="website"
                  value={
                    form.website
                  }
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
                Public contact
                information should be a
                service channel the
                organisation is
                comfortable sharing
                with referred citizens.
              </p>
            </div>
          </FormSection>

          {/* =================================================
              VERIFICATION PREPARATION
          ================================================= */}
          <FormSection
            icon={FileText}
            eyebrow="Section 05"
            title="Verification preparation"
            description="Supporting documents will eventually help Sauti Yo verify organisations before referrals are enabled."
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
                Document upload is not
                active yet.
              </p>

              <p className="mt-2 text-xs leading-5 text-text-secondary">
                The interface is being
                prepared now. Actual
                verification documents
                should later be uploaded
                securely through the
                backend rather than
                stored in the browser.
              </p>
            </div>
          </FormSection>

          {/* =================================================
              SAVE / NEXT
          ================================================= */}
          <section className="sticky bottom-0 z-20 mt-6 border border-border bg-surface/95 p-4 shadow-[var(--shadow-soft)] backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {saved
                    ? "Draft saved"
                    : "Save your progress before continuing."}
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  Saved drafts are
                  restored when you
                  return to this page
                  during the current
                  browser session.
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
                  to="/partner/services"
                  className="btn-primary"
                >
                  Continue to Services
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
   FORM SECTION
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
  children: React.ReactNode;
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

/* =========================================================
   FIELD HELPERS
========================================================= */

function Field({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      {children}
    </div>
  );
}

function Label({
  htmlFor,
  required,
  children,
}: {
  htmlFor: string;
  required?: boolean;
  children: React.ReactNode;
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
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      onChange={(event) =>
        onChange(event.target.value)
      }
      placeholder={placeholder}
      className="min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
    />
  );
}

function HelperText({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <p className="text-xs leading-5 text-text-secondary">
      {children}
    </p>
  );
}

/* =========================================================
   VERIFICATION ITEM
========================================================= */

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
            Upload coming later
          </span>
        </div>
      </div>
    </div>
  );
}