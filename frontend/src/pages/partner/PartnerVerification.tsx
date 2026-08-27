import {
  AlertCircle,
  ArrowRight,
  Building2,
  Check,
  CheckCircle2,
  Clock3,
  FileCheck2,
  FileText,
  LoaderCircle,
  Scale,
  Trash2,
  Upload,
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
  getPartnerOrganisation,
  getPartnerServices,
  getPartnerVerification,
  submitPartnerVerification,
  uploadPartnerVerificationDocument,
  deletePartnerVerificationDocument,
} from "../../services/partners";

import type {
  PartnerOrganisation,
  PartnerServiceConfiguration,
  PartnerVerification,
  PartnerVerificationDocument,
  PartnerVerificationDocumentType,
} from "../../services/partners";

/* =========================================================
   PAGE
========================================================= */

export default function PartnerVerification() {
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
    declarationAccurate,
    setDeclarationAccurate,
  ] =
    useState(false);

  const [
    declarationAuthorised,
    setDeclarationAuthorised,
  ] =
    useState(false);

  const [
    declarationConsent,
    setDeclarationConsent,
  ] =
    useState(false);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    submitting,
    setSubmitting,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState("");

  const [
    success,
    setSuccess,
  ] =
    useState("");

  const [
    uploadingType,
    setUploadingType,
  ] =
    useState<PartnerVerificationDocumentType | null>(
      null,
    );

  const [
    deletingDocumentId,
    setDeletingDocumentId,
  ] =
    useState<number | null>(
      null,
    );

  /* =======================================================
     LOAD VERIFICATION DATA
  ======================================================= */

  useEffect(() => {
    if (!organisationId) {
      setLoading(false);
      return;
    }

    const activeOrganisationId =
      organisationId;

    let active = true;

    async function loadVerificationPage() {
      setLoading(true);
      setError("");

      try {
        const [
          organisationData,
          servicesData,
          verificationData,
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

        if (verificationData) {
          setDeclarationAccurate(
            verificationData
              .declaration_accurate,
          );

          setDeclarationAuthorised(
            verificationData
              .declaration_authorised,
          );

          setDeclarationConsent(
            verificationData
              .declaration_consent,
          );
        }
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
            "Unable to load verification information.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadVerificationPage();

    return () => {
      active = false;
    };
  }, [organisationId]);

  /* =======================================================
     VERIFICATION EVIDENCE
  ======================================================= */

  async function refreshVerification() {
    if (!organisationId) {
      return;
    }

    const verificationData =
      await getPartnerVerification(
        organisationId,
      );

    setVerification(
      verificationData,
    );
  }

  async function handleEvidenceUpload(
    documentType: PartnerVerificationDocumentType,
    file: File,
  ) {
    if (!organisationId) {
      return;
    }

    setUploadingType(
      documentType,
    );

    setError("");
    setSuccess("");

    try {
      await uploadPartnerVerificationDocument(
        organisationId,
        documentType,
        file,
        file.name,
      );

      await refreshVerification();

      setSuccess(
        `${file.name} uploaded successfully.`,
      );
    } catch (caughtError) {
      if (
        caughtError instanceof ApiError
      ) {
        setError(
          caughtError.message,
        );
      } else {
        setError(
          "Unable to upload verification evidence.",
        );
      }
    } finally {
      setUploadingType(
        null,
      );
    }
  }

  async function handleEvidenceDelete(
    document: PartnerVerificationDocument,
  ) {
    if (!organisationId) {
      return;
    }

    const confirmed =
      window.confirm(
        `Remove "${document.title}"?`,
      );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(
      document.id,
    );

    setError("");
    setSuccess("");

    try {
      await deletePartnerVerificationDocument(
        organisationId,
        document.id,
      );

      await refreshVerification();

      setSuccess(
        "Verification evidence removed.",
      );
    } catch (caughtError) {
      if (
        caughtError instanceof ApiError
      ) {
        setError(
          caughtError.message,
        );
      } else {
        setError(
          "Unable to remove verification evidence.",
        );
      }
    } finally {
      setDeletingDocumentId(
        null,
      );
    }
  }

  /* =======================================================
     READINESS
  ======================================================= */

  const profileChecks =
    useMemo(() => {
      if (!organisation) {
        return {
          complete: false,
          percentage: 0,
        };
      }

      const values = [
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

      const completed =
        values.filter(
          (value) =>
            String(
              value ?? "",
            ).trim() !== "",
        ).length;

      const percentage =
        Math.round(
          (
            completed /
            values.length
          ) * 100,
        );

      return {
        complete:
          completed ===
          values.length,

        percentage,
      };
    }, [organisation]);

  const serviceChecks =
    useMemo(() => {
      if (!services) {
        return {
          complete: false,
          percentage: 0,
        };
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

      const completed =
        checks.filter(
          Boolean,
        ).length;

      const percentage =
        Math.round(
          (
            completed /
            checks.length
          ) * 100,
        );

      return {
        complete:
          completed ===
          checks.length,

        percentage,
      };
    }, [services]);

  const setupReady =
    profileChecks.complete &&
    serviceChecks.complete;

  const declarationsReady =
    declarationAccurate &&
    declarationAuthorised &&
    declarationConsent;

  function documentsForType(
    documentType: PartnerVerificationDocumentType,
  ) {
    return (
      verification?.documents ?? []
    ).filter(
      (document) =>
        document.document_type ===
        documentType,
    );
  }

  const alreadySubmitted =
    verification !== null &&
    [
      "submitted",
      "under_review",
      "verified",
    ].includes(
      verification.status,
    );

  const canSubmit =
    setupReady &&
    declarationsReady &&
    !alreadySubmitted &&
    !submitting;

  /* =======================================================
     SUBMIT
  ======================================================= */

  async function handleSubmit() {
    if (!organisationId) {
      setError(
        "No organisation is connected to this account.",
      );
      return;
    }

    if (!setupReady) {
      setError(
        "Complete your Organisation Profile and Services before submitting for verification.",
      );
      return;
    }

    if (!declarationsReady) {
      setError(
        "All three declarations must be accepted before verification can be submitted.",
      );
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const response =
        await submitPartnerVerification(
          organisationId,
          {
            declaration_accurate:
              declarationAccurate,

            declaration_authorised:
              declarationAuthorised,

            declaration_consent:
              declarationConsent,
          },
        );

      setVerification(
        response,
      );

      setSuccess(
        "Your organisation has been submitted for verification.",
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
          "Unable to submit the verification request.",
        );
      }
    } finally {
      setSubmitting(false);
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
            Loading verification
            status...
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
                Trust & verification
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Verification
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Review your
                organisation setup and
                submit the declarations
                required for Sauti Yo
                verification.
              </p>
            </div>

            <VerificationStatusBadge
              verification={
                verification
              }
            />
          </div>
        </div>
      </section>

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

          {/* SUCCESS */}

          {success && (
            <div className="mb-6 flex items-start gap-3 border border-success/30 bg-success/5 p-4">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />

              <p className="text-sm leading-6 text-success">
                {success}
              </p>
            </div>
          )}

          {/* EXISTING STATUS */}

          {verification && (
            <section className="mb-6 border border-border bg-surface p-5 sm:p-6">
              <div className="flex items-start gap-4">
                <StatusIcon
                  status={
                    verification.status
                  }
                />

                <div className="flex-1">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                    Verification status
                  </p>

                  <h2 className="mt-2 text-xl font-semibold text-text-primary">
                    {formatStatus(
                      verification.status,
                    )}
                  </h2>

                  {verification
                    .submitted_at && (
                    <p className="mt-2 text-sm leading-6 text-text-secondary">
                      Submitted{" "}
                      {formatDate(
                        verification
                          .submitted_at,
                      )}
                    </p>
                  )}

                  {verification
                    .review_notes && (
                    <div className="mt-4 border-l-2 border-gold bg-gold/5 p-4">
                      <p className="text-sm font-semibold text-text-primary">
                        Review note
                      </p>

                      <p className="mt-2 text-sm leading-6 text-text-secondary">
                        {
                          verification
                            .review_notes
                        }
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* READINESS */}

          <VerificationSection
            eyebrow="Section 01"
            title="Verification readiness"
            description="Your organisation profile and service information must be complete before a verification request can be submitted."
          >
            <div className="grid gap-4 md:grid-cols-2">
              <ReadinessCard
                icon={Building2}
                title="Organisation profile"
                description="Organisation identity, location and basic information."
                percentage={
                  profileChecks.percentage
                }
                complete={
                  profileChecks.complete
                }
                link="/partner/profile"
              />

              <ReadinessCard
                icon={Scale}
                title="Service configuration"
                description="Rights categories, support types, languages and service coverage."
                percentage={
                  serviceChecks.percentage
                }
                complete={
                  serviceChecks.complete
                }
                link="/partner/services"
              />
            </div>
          </VerificationSection>

          {/* SUPPORTING EVIDENCE */}

          <VerificationSection
            eyebrow="Section 02"
            title="Supporting evidence"
            description="Verification should be supported by appropriate organisation documentation rather than self-declaration alone."
          >
            <div className="grid gap-4 md:grid-cols-2">
              <EvidenceCard
                title="Registration evidence"
                description="Certificate, registration record or other documentation showing the organisation's legal or formal identity."
                documentType="registration"
                documents={documentsForType("registration")}
                uploading={uploadingType === "registration"}
                deletingDocumentId={deletingDocumentId}
                onUpload={handleEvidenceUpload}
                onDelete={handleEvidenceDelete}
              />

              <EvidenceCard
                title="Organisation identification"
                description="Additional documentation that helps confirm the organisation's identity and operating status."
                documentType="organisation_identification"
                documents={documentsForType("organisation_identification")}
                uploading={
                  uploadingType ===
                  "organisation_identification"
                }
                deletingDocumentId={deletingDocumentId}
                onUpload={handleEvidenceUpload}
                onDelete={handleEvidenceDelete}
              />

              <EvidenceCard
                title="Service evidence"
                description="Where appropriate, evidence that the organisation is capable of providing the services described in its profile."
                documentType="service_evidence"
                documents={documentsForType("service_evidence")}
                uploading={uploadingType === "service_evidence"}
                deletingDocumentId={deletingDocumentId}
                onUpload={handleEvidenceUpload}
                onDelete={handleEvidenceDelete}
              />

              <EvidenceCard
                title="Authorised representative"
                description="Information confirming that the person submitting the verification request is authorised to act for the organisation."
                documentType="authorised_representative"
                documents={
                  documentsForType(
                    "authorised_representative",
                  )
                }
                uploading={
                  uploadingType ===
                  "authorised_representative"
                }
                deletingDocumentId={deletingDocumentId}
                onUpload={handleEvidenceUpload}
                onDelete={handleEvidenceDelete}
              />
            </div>

            <div className="mt-5 flex items-start gap-3 border-l-2 border-gold bg-gold/5 p-4">
              <Upload className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <div>
                <p className="text-sm font-semibold text-text-primary">
                  Secure upload is the
                  next backend step.
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  The verification
                  document model already
                  exists. We will connect
                  real file upload after
                  the declaration and
                  submission workflow is
                  confirmed.
                </p>
              </div>
            </div>
          </VerificationSection>

          {/* DECLARATIONS */}

          <VerificationSection
            eyebrow="Section 03"
            title="Organisation declarations"
            description="Confirm the declarations below before submitting a verification request."
          >
            <div className="space-y-3">
              <DeclarationItem
                checked={
                  declarationAccurate
                }
                disabled={
                  alreadySubmitted
                }
                onChange={
                  setDeclarationAccurate
                }
                title="The information provided is accurate."
                description="I confirm that the organisation profile and service information is accurate to the best of my knowledge."
              />

              <DeclarationItem
                checked={
                  declarationAuthorised
                }
                disabled={
                  alreadySubmitted
                }
                onChange={
                  setDeclarationAuthorised
                }
                title="I am authorised to submit this request."
                description="I confirm that I am authorised to provide this information and submit a verification request on behalf of the organisation."
              />

              <DeclarationItem
                checked={
                  declarationConsent
                }
                disabled={
                  alreadySubmitted
                }
                onChange={
                  setDeclarationConsent
                }
                title="The organisation agrees to verification review."
                description="I understand that Sauti Yo may review the organisation's information and request additional evidence before approving referral eligibility."
              />
            </div>
          </VerificationSection>

          {/* SUBMIT */}

          <section className="mt-6 border border-border bg-surface p-5 sm:p-6">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Final step
                </p>

                <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                  {alreadySubmitted
                    ? "Verification request submitted"
                    : "Submit for review"}
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
                  {alreadySubmitted
                    ? "Your organisation's verification request is now part of the Sauti Yo review workflow."
                    : setupReady
                      ? "Your setup is complete. Accept all declarations to submit your organisation for verification."
                      : "Complete both your Organisation Profile and Services before verification can be submitted."}
                </p>
              </div>

              <button
                type="button"
                onClick={
                  handleSubmit
                }
                disabled={
                  !canSubmit
                }
                className="btn-primary disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? (
                  <>
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : alreadySubmitted ? (
                  <>
                    <Check className="h-4 w-4" />
                    Submitted
                  </>
                ) : (
                  <>
                    <FileCheck2 className="h-4 w-4" />
                    Submit for Verification
                  </>
                )}
              </button>
            </div>
          </section>

          {/* REVIEW PROCESS */}

          <section className="mt-6 border border-border bg-surface p-6 sm:p-7">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
              What happens next
            </p>

            <div className="mt-5 grid gap-5 lg:grid-cols-[1.2fr_2fr]">
              <div>
                <h2 className="heading-serif text-3xl font-semibold text-text-primary">
                  Verification is a
                  review process,
                  <span className="block text-gold-deep dark:text-gold">
                    not an automatic
                    status.
                  </span>
                </h2>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <ProcessStep
                  number="01"
                  title="Submit"
                  description="The organisation submits its profile, declarations and supporting evidence."
                />

                <ProcessStep
                  number="02"
                  title="Review"
                  description="An authorised reviewer checks the information and may request clarification."
                />

                <ProcessStep
                  number="03"
                  title="Decision"
                  description="The organisation may be verified, returned for changes, or declined based on the review."
                />
              </div>
            </div>
          </section>

          {verification?.status ===
            "verified" && (
            <section className="mt-6 border border-success/30 bg-success/5 p-5 sm:p-6">
              <div className="flex items-start gap-4">
                <CheckCircle2 className="mt-1 h-6 w-6 shrink-0 text-success" />

                <div>
                  <h2 className="text-lg font-semibold text-text-primary">
                    Organisation verified
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    Your organisation
                    has completed the
                    verification review.
                    Referral eligibility
                    can now be determined
                    using your current
                    service configuration
                    and capacity.
                  </p>

                  <Link
                    to="/partner/referrals"
                    className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-gold-deep dark:text-gold"
                  >
                    Go to Referrals

                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

/* =========================================================
   COMPONENTS
========================================================= */

function VerificationSection({
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

function ReadinessCard({
  icon: Icon,
  title,
  description,
  percentage,
  complete,
  link,
}: {
  icon: typeof Building2;
  title: string;
  description: string;
  percentage: number;
  complete: boolean;
  link: string;
}) {
  return (
    <div className="border border-border bg-background p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gold/10 text-gold">
          <Icon className="h-5 w-5" />
        </div>

        {complete ? (
          <CheckCircle2 className="h-5 w-5 text-success" />
        ) : (
          <Clock3 className="h-5 w-5 text-gold" />
        )}
      </div>

      <h3 className="mt-4 font-semibold text-text-primary">
        {title}
      </h3>

      <p className="mt-2 text-sm leading-6 text-text-secondary">
        {description}
      </p>

      <div className="mt-5">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-text-secondary">
            Completion
          </span>

          <span className="text-gold-deep dark:text-gold">
            {percentage}%
          </span>
        </div>

        <div className="mt-2 h-1.5 overflow-hidden bg-border">
          <div
            className="h-full bg-gold"
            style={{
              width:
                `${percentage}%`,
            }}
          />
        </div>
      </div>

      <Link
        to={link}
        className="mt-5 inline-flex items-center gap-2 text-xs font-semibold text-text-primary"
      >
        {complete
          ? "Review details"
          : "Complete section"}

        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}

function EvidenceCard({
  title,
  description,
  documentType,
  documents,
  uploading,
  deletingDocumentId,
  onUpload,
  onDelete,
}: {
  title: string;
  description: string;
  documentType: PartnerVerificationDocumentType;
  documents: PartnerVerificationDocument[];
  uploading: boolean;
  deletingDocumentId: number | null;
  onUpload: (
    documentType: PartnerVerificationDocumentType,
    file: File,
  ) => Promise<void>;
  onDelete: (
    document: PartnerVerificationDocument,
  ) => Promise<void>;
}) {
  const inputId =
    `verification-${documentType}`;

  return (
    <div className="border border-border bg-background p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <FileText className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-text-primary">
            {title}
          </h3>

          <p className="mt-2 text-xs leading-5 text-text-secondary">
            {description}
          </p>

          <input
            id={inputId}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
            className="hidden"
            disabled={uploading}
            onChange={(event) => {
              const file =
                event.target.files?.[0];

              if (!file) {
                return;
              }

              void onUpload(
                documentType,
                file,
              );

              event.currentTarget.value =
                "";
            }}
          />

          <label
            htmlFor={inputId}
            className={[
              "mt-4 inline-flex cursor-pointer items-center gap-2 border border-border px-3 py-2 text-xs font-semibold transition",
              uploading
                ? "pointer-events-none opacity-50"
                : "hover:border-gold hover:text-gold-deep dark:hover:text-gold",
            ].join(" ")}
          >
            {uploading ? (
              <>
                <LoaderCircle className="h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Select upload
              </>
            )}
          </label>

          <p className="mt-2 text-[11px] text-text-secondary">
            PDF, JPG or PNG · Maximum 10 MB
          </p>

          {documents.length > 0 && (
            <div className="mt-4 space-y-2">
              {documents.map(
                (document) => (
                  <div
                    key={document.id}
                    className="flex items-center justify-between gap-3 border border-border bg-surface px-3 py-2"
                  >
                    <div className="min-w-0">
                      <a
                        href={document.file}
                        target="_blank"
                        rel="noreferrer"
                        className="block truncate text-xs font-semibold text-text-primary hover:text-gold-deep dark:hover:text-gold"
                      >
                        {document.title}
                      </a>

                      <p className="mt-1 text-[10px] text-text-secondary">
                        Uploaded{" "}
                        {formatDate(
                          document.uploaded_at,
                        )}
                      </p>
                    </div>

                    <button
                      type="button"
                      title="Remove document"
                      disabled={
                        deletingDocumentId ===
                        document.id
                      }
                      onClick={() =>
                        void onDelete(
                          document,
                        )
                      }
                      className="shrink-0 border border-border p-2 text-text-secondary transition hover:border-red-300 hover:text-red-600 disabled:opacity-40"
                    >
                      {deletingDocumentId ===
                      document.id ? (
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DeclarationItem({
  checked,
  disabled,
  onChange,
  title,
  description,
}: {
  checked: boolean;
  disabled: boolean;
  onChange:
    (checked: boolean) => void;
  title: string;
  description: string;
}) {
  return (
    <label
      className={[
        "flex items-start gap-4 border p-4 transition",
        checked
          ? "border-gold bg-gold/5"
          : "border-border bg-background",
        disabled
          ? "cursor-default opacity-75"
          : "cursor-pointer",
      ].join(" ")}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) =>
          onChange(
            event.target.checked,
          )
        }
        className="mt-1 h-4 w-4 shrink-0 accent-[#c99522]"
      />

      <div>
        <p className="font-semibold text-text-primary">
          {title}
        </p>

        <p className="mt-1 text-sm leading-6 text-text-secondary">
          {description}
        </p>
      </div>
    </label>
  );
}

function VerificationStatusBadge({
  verification,
}: {
  verification:
    | PartnerVerification
    | null;
}) {
  if (!verification) {
    return (
      <span className="inline-flex items-center gap-2 border border-border px-3 py-2 text-xs font-semibold text-text-secondary">
        <Clock3 className="h-4 w-4 text-gold" />
        Not submitted
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2 border border-gold/40 bg-gold/5 px-3 py-2 text-xs font-semibold text-text-primary">
      <StatusIcon
        status={
          verification.status
        }
        compact
      />

      {formatStatus(
        verification.status,
      )}
    </span>
  );
}

function StatusIcon({
  status,
  compact = false,
}: {
  status: string;
  compact?: boolean;
}) {
  const iconClass =
    compact
      ? "h-4 w-4"
      : "h-6 w-6";

  if (status === "verified") {
    return (
      <CheckCircle2
        className={`${iconClass} text-success`}
      />
    );
  }

  if (
    status === "submitted" ||
    status === "under_review"
  ) {
    return (
      <Clock3
        className={`${iconClass} text-gold`}
      />
    );
  }

  return (
    <AlertCircle
      className={`${iconClass} text-text-secondary`}
    />
  );
}

function ProcessStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <p className="text-xs font-bold text-gold-deep dark:text-gold">
        {number}
      </p>

      <h3 className="mt-2 font-semibold text-text-primary">
        {title}
      </h3>

      <p className="mt-2 text-xs leading-5 text-text-secondary">
        {description}
      </p>
    </div>
  );
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
  value: string,
) {
  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleString();
}
