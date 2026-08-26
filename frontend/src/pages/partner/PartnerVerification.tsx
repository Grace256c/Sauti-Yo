import {
  AlertCircle,
  ArrowLeft,
  Check,
  CheckCircle2,
  Clock3,
  FileCheck2,
  FileText,
  LockKeyhole,
  Send,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

type VerificationState =
  | "not-ready"
  | "ready"
  | "submitted"
  | "changes-requested"
  | "verified"
  | "rejected";

type SavedProfile = {
  organisationName?: string;
  organisationType?: string;
  registrationNumber?: string;
  description?: string;
  contactName?: string;
  contactRole?: string;
  contactEmail?: string;
  contactPhone?: string;
  headquartersDistrict?: string;
  physicalAddress?: string;
};

type SavedServices = {
  categories?: string[];
  supportTypes?: string[];
  languages?: string[];
  supportChannels?: string[];
  districtsServed?: string[];
  nationwide?: boolean;
  serviceDescription?: string;
};

type VerificationDraft = {
  declarationAccurate: boolean;
  declarationAuthorised: boolean;
  declarationConsent: boolean;
  submittedAt?: string;
  status: VerificationState;
};

const PROFILE_STORAGE_KEY =
  "sauti-yo-partner-profile-draft";

const SERVICES_STORAGE_KEY =
  "sauti-yo-partner-services-draft";

const VERIFICATION_STORAGE_KEY =
  "sauti-yo-partner-verification-draft";

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

function calculateProfileCompletion(
  profile: SavedProfile | null,
) {
  if (!profile) {
    return 0;
  }

  const required = [
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

  const completed =
    required.filter(
      (value) =>
        typeof value === "string" &&
        value.trim() !== "",
    ).length;

  return Math.round(
    (completed / required.length) *
      100,
  );
}

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

  return Math.round(
    (checks.filter(Boolean).length /
      checks.length) *
      100,
  );
}

function loadVerificationDraft():
  VerificationDraft {
  try {
    const stored =
      sessionStorage.getItem(
        VERIFICATION_STORAGE_KEY,
      );

    if (!stored) {
      return {
        declarationAccurate: false,
        declarationAuthorised: false,
        declarationConsent: false,
        status: "not-ready",
      };
    }

    const parsed =
      JSON.parse(
        stored,
      ) as Partial<VerificationDraft>;

    return {
      declarationAccurate:
        parsed.declarationAccurate ??
        false,

      declarationAuthorised:
        parsed.declarationAuthorised ??
        false,

      declarationConsent:
        parsed.declarationConsent ??
        false,

      submittedAt:
        parsed.submittedAt,

      status:
        parsed.status ??
        "not-ready",
    };
  } catch {
    return {
      declarationAccurate: false,
      declarationAuthorised: false,
      declarationConsent: false,
      status: "not-ready",
    };
  }
}

export default function PartnerVerification() {
  const profile =
    useMemo(
      () =>
        readSessionDraft<SavedProfile>(
          PROFILE_STORAGE_KEY,
        ),
      [],
    );

  const services =
    useMemo(
      () =>
        readSessionDraft<SavedServices>(
          SERVICES_STORAGE_KEY,
        ),
      [],
    );

  const profileCompletion =
    calculateProfileCompletion(profile);

  const servicesCompletion =
    calculateServicesCompletion(
      services,
    );

  const prerequisitesReady =
    profileCompletion === 100 &&
    servicesCompletion === 100;

  const [
    verification,
    setVerification,
  ] =
    useState<VerificationDraft>(
      loadVerificationDraft,
    );

  const declarationsComplete =
    verification.declarationAccurate &&
    verification.declarationAuthorised &&
    verification.declarationConsent;

  const canSubmit =
    prerequisitesReady &&
    declarationsComplete &&
    verification.status !==
      "submitted" &&
    verification.status !==
      "verified";

  const updateDeclaration = (
    key:
      | "declarationAccurate"
      | "declarationAuthorised"
      | "declarationConsent",
    checked: boolean,
  ) => {
    setVerification((current) => {
      const next = {
        ...current,
        [key]: checked,
        status:
          prerequisitesReady
            ? "ready"
            : "not-ready",
      } as VerificationDraft;

      sessionStorage.setItem(
        VERIFICATION_STORAGE_KEY,
        JSON.stringify(next),
      );

      return next;
    });
  };

  const handleSubmit = () => {
    if (!canSubmit) {
      return;
    }

    const next: VerificationDraft = {
      ...verification,
      status: "submitted",
      submittedAt:
        new Date().toISOString(),
    };

    /*
     * IMPORTANT:
     *
     * This prototype only stores a submission state.
     * It does NOT verify the organisation.
     *
     * Real verification must be reviewed by an authorised
     * backend/admin process.
     */
    sessionStorage.setItem(
      VERIFICATION_STORAGE_KEY,
      JSON.stringify(next),
    );

    setVerification(next);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
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
                Trust & verification
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Verification
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Review your organisation
                setup and prepare the
                information required for
                Sauti Yo verification.
              </p>
            </div>

            <VerificationBadge
              status={
                verification.status
              }
              prerequisitesReady={
                prerequisitesReady
              }
            />
          </div>
        </div>
      </section>

      {/* =====================================================
          BODY
      ===================================================== */}
      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">
          {/* =================================================
              SUBMITTED STATE
          ================================================= */}
          {verification.status ===
            "submitted" && (
            <section className="relative overflow-hidden border border-gold/40 bg-gold/5 p-6 sm:p-7">
              <div className="absolute inset-y-0 left-0 w-1 bg-gold" />

              <div className="flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/15 text-gold">
                  <Clock3
                    className="h-5 w-5"
                    strokeWidth={1.7}
                  />
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                    Submitted
                  </p>

                  <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary sm:text-3xl">
                    Your verification
                    request is ready for
                    review.
                  </h2>

                  <p className="mt-3 max-w-3xl text-sm leading-6 text-text-secondary">
                    In the production
                    system, an authorised
                    reviewer would now
                    assess the
                    organisation's
                    information and
                    supporting evidence.
                    Submitting this form
                    does not automatically
                    verify the
                    organisation.
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* =================================================
              READINESS
          ================================================= */}
          <section className="mt-6 border border-border bg-surface">
            <div className="border-b border-border p-6 sm:p-7">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                  <FileCheck2
                    className="h-5 w-5"
                    strokeWidth={1.7}
                  />
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                    Section 01
                  </p>

                  <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                    Verification
                    readiness
                  </h2>

                  <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                    Your organisation
                    profile and services
                    must be complete
                    before a verification
                    request can be
                    submitted.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 p-6 sm:p-7 md:grid-cols-2">
              <ReadinessCard
                title="Organisation profile"
                completion={
                  profileCompletion
                }
                description="Organisation identity, contact and location information."
                to="/partner/profile"
              />

              <ReadinessCard
                title="Service configuration"
                completion={
                  servicesCompletion
                }
                description="Rights categories, support types, languages and service coverage."
                to="/partner/services"
              />
            </div>
          </section>

          {/* =================================================
              REQUIRED EVIDENCE
          ================================================= */}
          <section className="mt-6 border border-border bg-surface">
            <div className="border-b border-border p-6 sm:p-7">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                  <FileText
                    className="h-5 w-5"
                    strokeWidth={1.7}
                  />
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                    Section 02
                  </p>

                  <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                    Supporting evidence
                  </h2>

                  <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                    Verification should
                    be supported by
                    appropriate
                    organisation
                    documentation rather
                    than self-declaration
                    alone.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 p-6 sm:p-7 md:grid-cols-2">
              <EvidenceCard
                title="Registration evidence"
                description="Certificate, registration record or other documentation showing the organisation's legal or formal identity."
                required
              />

              <EvidenceCard
                title="Organisation identification"
                description="Additional documentation that helps confirm the organisation's identity and operating status."
                required
              />

              <EvidenceCard
                title="Service evidence"
                description="Where appropriate, evidence that the organisation is equipped to provide the services listed in its profile."
              />

              <EvidenceCard
                title="Authorised representative"
                description="Information confirming that the person submitting the verification request is authorised to act for the organisation."
                required
              />
            </div>

            <div className="mx-6 mb-6 border-l-2 border-gold bg-gold/5 p-4 sm:mx-7 sm:mb-7">
              <div className="flex items-start gap-3">
                <LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

                <div>
                  <p className="text-sm font-semibold text-text-primary">
                    Secure upload comes
                    with the backend.
                  </p>

                  <p className="mt-2 text-xs leading-5 text-text-secondary">
                    Verification
                    documents should not
                    be stored in
                    sessionStorage or
                    handled as ordinary
                    browser data. Upload
                    and review should be
                    implemented through a
                    secure authenticated
                    backend workflow.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* =================================================
              DECLARATIONS
          ================================================= */}
          <section className="mt-6 border border-border bg-surface">
            <div className="border-b border-border p-6 sm:p-7">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                  <ShieldCheck
                    className="h-5 w-5"
                    strokeWidth={1.7}
                  />
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                    Section 03
                  </p>

                  <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                    Organisation
                    declarations
                  </h2>

                  <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                    Confirm the
                    statements below
                    before submitting a
                    verification request.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4 p-6 sm:p-7">
              <Declaration
                checked={
                  verification.declarationAccurate
                }
                disabled={
                  verification.status ===
                  "submitted"
                }
                onChange={(checked) =>
                  updateDeclaration(
                    "declarationAccurate",
                    checked,
                  )
                }
                title="The information provided is accurate."
                description="I confirm that the organisation profile and service information is accurate to the best of my knowledge."
              />

              <Declaration
                checked={
                  verification.declarationAuthorised
                }
                disabled={
                  verification.status ===
                  "submitted"
                }
                onChange={(checked) =>
                  updateDeclaration(
                    "declarationAuthorised",
                    checked,
                  )
                }
                title="I am authorised to submit this request."
                description="I confirm that I am authorised to provide this information and submit a verification request on behalf of the organisation."
              />

              <Declaration
                checked={
                  verification.declarationConsent
                }
                disabled={
                  verification.status ===
                  "submitted"
                }
                onChange={(checked) =>
                  updateDeclaration(
                    "declarationConsent",
                    checked,
                  )
                }
                title="The organisation agrees to verification review."
                description="I understand that Sauti Yo may review the organisation's information and request additional evidence before approving referral eligibility."
              />
            </div>
          </section>

          {/* =================================================
              SUBMIT
          ================================================= */}
          <section className="mt-6 border border-border bg-surface">
            <div className="grid gap-8 p-6 sm:p-7 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Final step
                </p>

                <h2 className="heading-serif mt-3 text-2xl font-semibold text-text-primary">
                  Submit for review
                </h2>

                {!prerequisitesReady ? (
                  <div className="mt-4 flex max-w-2xl items-start gap-3">
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                    <p className="text-sm leading-6 text-text-secondary">
                      Complete both your
                      Organisation Profile
                      and Services before
                      verification can be
                      submitted.
                    </p>
                  </div>
                ) : !declarationsComplete ? (
                  <div className="mt-4 flex max-w-2xl items-start gap-3">
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                    <p className="text-sm leading-6 text-text-secondary">
                      Review and accept
                      all three
                      declarations before
                      submitting.
                    </p>
                  </div>
                ) : verification.status ===
                  "submitted" ? (
                  <div className="mt-4 flex max-w-2xl items-start gap-3">
                    <Clock3 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                    <p className="text-sm leading-6 text-text-secondary">
                      Your verification
                      request has been
                      submitted and is
                      awaiting review.
                    </p>
                  </div>
                ) : (
                  <div className="mt-4 flex max-w-2xl items-start gap-3">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                    <p className="text-sm leading-6 text-text-secondary">
                      Your organisation
                      setup is ready to
                      submit for
                      verification
                      review.
                    </p>
                  </div>
                )}
              </div>

              <button
                type="button"
                disabled={!canSubmit}
                onClick={handleSubmit}
                className={[
                  "inline-flex min-h-12 w-full items-center justify-center gap-2 px-7 py-3 font-bold transition lg:w-auto",

                  canSubmit
                    ? "bg-gold text-[#191919] hover:-translate-y-0.5"
                    : "cursor-not-allowed bg-border text-text-secondary opacity-60",
                ].join(" ")}
              >
                {verification.status ===
                "submitted" ? (
                  <>
                    <Clock3 className="h-4 w-4" />
                    Submitted
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Submit for Verification
                  </>
                )}
              </button>
            </div>
          </section>

          {/* =================================================
              WORKFLOW
          ================================================= */}
          <section className="mt-6 border border-border bg-surface">
            <div className="grid gap-8 p-6 sm:p-7 lg:grid-cols-[0.75fr_1.25fr] lg:items-start">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  What happens next
                </p>

                <h2 className="heading-serif mt-3 text-2xl font-semibold leading-tight text-text-primary sm:text-3xl">
                  Verification is a
                  review process,
                  <span className="block text-gold-deep dark:text-gold">
                    not an automatic
                    status.
                  </span>
                </h2>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <WorkflowStep
                  number="01"
                  title="Submit"
                  text="The organisation submits its profile, services, declarations and supporting evidence."
                />

                <WorkflowStep
                  number="02"
                  title="Review"
                  text="An authorised reviewer checks the organisation's information and may request clarification."
                />

                <WorkflowStep
                  number="03"
                  title="Decision"
                  text="The organisation may be verified, asked to make changes, or declined based on the review."
                />
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}

function VerificationBadge({
  status,
  prerequisitesReady,
}: {
  status: VerificationState;
  prerequisitesReady: boolean;
}) {
  let label = "Not ready";
  let Icon = LockKeyhole;

  if (
    prerequisitesReady &&
    status !== "submitted"
  ) {
    label = "Ready to submit";
    Icon = FileCheck2;
  }

  if (status === "submitted") {
    label = "Pending review";
    Icon = Clock3;
  }

  if (
    status ===
    "changes-requested"
  ) {
    label = "Changes requested";
    Icon = AlertCircle;
  }

  if (status === "verified") {
    label = "Verified";
    Icon = CheckCircle2;
  }

  if (status === "rejected") {
    label = "Not approved";
    Icon = XCircle;
  }

  return (
    <div className="inline-flex w-fit items-center gap-2 border border-gold/30 bg-gold/5 px-4 py-2.5 text-sm">
      <Icon className="h-4 w-4 text-gold" />

      <span className="font-semibold text-text-primary">
        {label}
      </span>
    </div>
  );
}

function ReadinessCard({
  title,
  completion,
  description,
  to,
}: {
  title: string;
  completion: number;
  description: string;
  to: string;
}) {
  const complete =
    completion === 100;

  return (
    <div className="border border-border bg-background p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gold/10 text-gold">
          {complete ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Clock3 className="h-4 w-4" />
          )}
        </div>

        <span className="text-sm font-semibold text-gold-deep dark:text-gold">
          {completion}%
        </span>
      </div>

      <h3 className="mt-4 font-semibold text-text-primary">
        {title}
      </h3>

      <p className="mt-2 text-sm leading-6 text-text-secondary">
        {description}
      </p>

      <div className="mt-4 h-1 overflow-hidden bg-border">
        <div
          className="h-full bg-gold"
          style={{
            width: `${completion}%`,
          }}
        />
      </div>

      {!complete && (
        <Link
          to={to}
          className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-gold-deep dark:text-gold"
        >
          Complete section
          <ArrowLeft className="h-4 w-4 rotate-180" />
        </Link>
      )}
    </div>
  );
}

function EvidenceCard({
  title,
  description,
  required,
}: {
  title: string;
  description: string;
  required?: boolean;
}) {
  return (
    <article className="border border-border bg-background p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <FileText
            className="h-4 w-4"
            strokeWidth={1.7}
          />
        </div>

        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-text-primary">
              {title}
            </h3>

            {required && (
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-gold-deep dark:text-gold">
                Required
              </span>
            )}
          </div>

          <p className="mt-2 text-xs leading-5 text-text-secondary">
            {description}
          </p>

          <span className="mt-4 inline-flex border border-border px-3 py-1.5 text-[11px] font-semibold text-text-secondary">
            Secure upload coming with backend
          </span>
        </div>
      </div>
    </article>
  );
}

function Declaration({
  checked,
  disabled,
  onChange,
  title,
  description,
}: {
  checked: boolean;
  disabled: boolean;
  onChange: (checked: boolean) => void;
  title: string;
  description: string;
}) {
  return (
    <label
      className={[
        "flex items-start gap-4 border p-5 transition",

        checked
          ? "border-gold bg-gold/5"
          : "border-border bg-background",

        disabled
          ? "cursor-not-allowed opacity-70"
          : "cursor-pointer hover:border-gold/60",
      ].join(" ")}
    >
      <span
        className={[
          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border",

          checked
            ? "border-gold bg-gold text-[#191919]"
            : "border-border",
        ].join(" ")}
      >
        {checked && (
          <Check className="h-3 w-3" />
        )}
      </span>

      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        disabled={disabled}
        onChange={(event) =>
          onChange(
            event.target.checked,
          )
        }
      />

      <div>
        <p className="font-semibold text-text-primary">
          {title}
        </p>

        <p className="mt-2 text-sm leading-6 text-text-secondary">
          {description}
        </p>
      </div>
    </label>
  );
}

function WorkflowStep({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="border-t border-border pt-4">
      <span className="text-xs font-bold text-gold">
        {number}
      </span>

      <h3 className="mt-3 font-semibold text-text-primary">
        {title}
      </h3>

      <p className="mt-2 text-xs leading-5 text-text-secondary">
        {text}
      </p>
    </div>
  );
}