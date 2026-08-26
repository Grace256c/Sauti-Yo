import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  LoaderCircle,
  MapPin,
  MessageSquareText,
  Phone,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Link,
  useParams,
} from "react-router-dom";

import {
  ApiError,
} from "../../services/api";

import {
  getReferral,
  updateReferralStatus,
} from "../../services/referrals";

import type {
  Referral,
} from "../../services/referrals";

/* =========================================================
   TYPES
========================================================= */

type ReferralStatus =
  | "new"
  | "reviewing"
  | "accepted"
  | "in_progress"
  | "completed"
  | "closed";

type StatusAction = {
  status: ReferralStatus;
  label: string;
  description: string;
};

const transitions: Record<
  ReferralStatus,
  StatusAction[]
> = {
  new: [
    {
      status: "reviewing",
      label: "Start review",
      description:
        "Mark this referral as being assessed by your organisation.",
    },
  ],

  reviewing: [
    {
      status: "accepted",
      label: "Accept referral",
      description:
        "Confirm that your organisation can support this citizen.",
    },
  ],

  accepted: [
    {
      status: "in_progress",
      label: "Start support",
      description:
        "Mark support as actively underway.",
    },
  ],

  in_progress: [
    {
      status: "completed",
      label: "Complete referral",
      description:
        "Confirm that support for this referral has been completed.",
    },
  ],

  completed: [],

  closed: [],
};

/* =========================================================
   HELPERS
========================================================= */

function normalizeStatus(
  status: string,
): ReferralStatus {
  if (
    status === "in-progress"
  ) {
    return "in_progress";
  }

  if (
    [
      "new",
      "reviewing",
      "accepted",
      "in_progress",
      "completed",
      "closed",
    ].includes(status)
  ) {
    return status as ReferralStatus;
  }

  return "new";
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

  return date.toLocaleString();
}

/* =========================================================
   PAGE
========================================================= */

export default function PartnerReferralDetail() {
  const {
    referralId,
  } = useParams();

  const id =
    Number(referralId);

  const [
    referral,
    setReferral,
  ] =
    useState<Referral | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    updating,
    setUpdating,
  ] =
    useState(false);

  const [
    note,
    setNote,
  ] =
    useState("");

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

  /* =======================================================
     LOAD
  ======================================================= */

  useEffect(() => {
    if (
      !Number.isInteger(id) ||
      id <= 0
    ) {
      setError(
        "Invalid referral ID.",
      );
      setLoading(false);
      return;
    }

    let active = true;

    async function loadReferral() {
      setLoading(true);
      setError("");

      try {
        const data =
          await getReferral(id);

        if (!active) {
          return;
        }

        setReferral(data);
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
            "Unable to load this referral.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadReferral();

    return () => {
      active = false;
    };
  }, [id]);

  /* =======================================================
     STATUS
  ======================================================= */

  const currentStatus =
    useMemo(
      () =>
        normalizeStatus(
          referral?.status ?? "new",
        ),
      [referral],
    );

  const availableActions =
    transitions[currentStatus];

  async function changeStatus(
    nextStatus: ReferralStatus,
  ) {
    if (!referral) {
      return;
    }

    setUpdating(true);
    setError("");
    setSuccess("");

    try {
      const updated =
        await updateReferralStatus(
          referral.id,
          {
            status: nextStatus,
            note:
              note.trim() ||
              `Referral moved to ${formatStatus(nextStatus)}.`,
          },
        );

      setReferral(updated);
      setNote("");

      setSuccess(
        `Referral status updated to ${formatStatus(
          nextStatus,
        )}.`,
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
          "Unable to update referral status.",
        );
      }
    } finally {
      setUpdating(false);
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
            Loading referral...
          </p>
        </div>
      </div>
    );
  }

  if (
    !referral
  ) {
    return (
      <div className="px-5 py-10 sm:px-8 lg:px-10 xl:px-12">
        <div className="mx-auto max-w-5xl">
          <div className="border border-danger/30 bg-danger/5 p-5">
            <AlertCircle className="h-5 w-5 text-danger" />

            <p className="mt-3 text-sm text-danger">
              {error ||
                "Referral not found."}
            </p>

            <Link
              to="/partner/referrals"
              className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-text-primary"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to referrals
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* HEADER */}

      <section className="border-b border-border bg-surface">
        <div className="px-5 py-8 sm:px-8 lg:px-10 lg:py-9 xl:px-12">
          <Link
            to="/partner/referrals"
            className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to referrals
          </Link>

          <div className="mt-6 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Referral review
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                {referral.reference}
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Review the shared referral information and keep the referral status current as support progresses.
              </p>
            </div>

            <StatusBadge
              status={
                currentStatus
              }
            />
          </div>
        </div>
      </section>

      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">

          {error && (
            <div className="mb-5 flex items-start gap-3 border border-danger/30 bg-danger/5 p-4">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />

              <p className="text-sm text-danger">
                {error}
              </p>
            </div>
          )}

          {success && (
            <div className="mb-5 flex items-start gap-3 border border-success/30 bg-success/5 p-4">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />

              <p className="text-sm text-success">
                {success}
              </p>
            </div>
          )}

          {/* PRIVACY */}

          <section className="border border-border bg-surface p-5 sm:p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                <ShieldCheck className="h-5 w-5" />
              </div>

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Citizen privacy
                </p>

                <h2 className="mt-2 font-semibold text-text-primary">
                  Use only the information shared for this referral.
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                  This record should contain only the information needed to assess and provide the requested support.
                </p>
              </div>
            </div>
          </section>

          {/* REFERRAL DETAILS */}

          <section className="mt-6 border border-border bg-surface">
            <div className="border-b border-border p-6 sm:p-7">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                Referral information
              </p>

              <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                Shared case details
              </h2>
            </div>

            <div className="grid gap-5 p-6 sm:p-7 md:grid-cols-2">
              <InfoItem
                icon={UserRound}
                label="Reference"
                value={
                  referral.reference
                }
              />

              <InfoItem
                icon={MapPin}
                label="District"
                value={
                  referral.district ||
                  "Not specified"
                }
              />

              <InfoItem
                icon={MessageSquareText}
                label="Language"
                value={
                  referral.language ||
                  "Not specified"
                }
              />

              <InfoItem
                icon={Phone}
                label="Preferred support channel"
                value={
                  referral.preferred_support_channel ||
                  "Not specified"
                }
              />

              <InfoItem
                icon={Clock3}
                label="Created"
                value={
                  formatDate(
                    referral.created_at,
                  )
                }
              />

              <InfoItem
                icon={ShieldCheck}
                label="Citizen consent"
                value={
                  referral.citizen_consent_to_share
                    ? "Consent recorded"
                    : "Consent not recorded"
                }
              />

              <div className="md:col-span-2">
                <p className="text-sm font-semibold text-text-primary">
                  Referral summary
                </p>

                <div className="mt-2 border border-border bg-background p-4">
                  <p className="text-sm leading-6 text-text-secondary">
                    {referral.summary ||
                      "No summary provided."}
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* STATUS UPDATE */}

          <section className="mt-6 border border-border bg-surface">
            <div className="border-b border-border p-6 sm:p-7">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                Referral workflow
              </p>

              <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                Update referral status
              </h2>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                Keep the status aligned with what is actually happening with the referral.
              </p>
            </div>

            <div className="p-6 sm:p-7">
              {availableActions.length >
              0 ? (
                <>
                  <label className="block">
                    <span className="text-sm font-semibold text-text-primary">
                      Status note
                    </span>

                    <textarea
                      rows={4}
                      value={note}
                      onChange={(event) =>
                        setNote(
                          event.target.value,
                        )
                      }
                      placeholder="Add a short note about this status change."
                      className="mt-2 w-full resize-y border border-border bg-background px-4 py-3 text-sm leading-6 text-text-primary outline-none focus:border-gold"
                    />
                  </label>

                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    {availableActions.map(
                      (action) => (
                        <button
                          key={
                            action.status
                          }
                          type="button"
                          disabled={
                            updating
                          }
                          onClick={() =>
                            void changeStatus(
                              action.status,
                            )
                          }
                          className="border border-gold bg-gold/5 p-5 text-left transition hover:bg-gold/10 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <p className="font-semibold text-text-primary">
                            {action.label}
                          </p>

                          <p className="mt-2 text-sm leading-6 text-text-secondary">
                            {
                              action.description
                            }
                          </p>

                          <span className="mt-4 inline-flex items-center gap-2 text-xs font-bold text-gold-deep dark:text-gold">
                            {updating
                              ? "Updating..."
                              : "Continue"}

                            {updating ? (
                              <LoaderCircle className="h-4 w-4 animate-spin" />
                            ) : (
                              <CheckCircle2 className="h-4 w-4" />
                            )}
                          </span>
                        </button>
                      ),
                    )}
                  </div>
                </>
              ) : (
                <div className="flex items-start gap-4 border border-border bg-background p-5">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />

                  <div>
                    <p className="font-semibold text-text-primary">
                      No further status action is required.
                    </p>

                    <p className="mt-2 text-sm leading-6 text-text-secondary">
                      This referral is currently marked as {formatStatus(currentStatus)}.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* HISTORY */}

          <section className="mt-6 border border-border bg-surface">
            <div className="border-b border-border p-6 sm:p-7">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                Audit trail
              </p>

              <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                Status history
              </h2>
            </div>

            <div className="divide-y divide-border">
              {referral.status_history.length >
              0 ? (
                referral.status_history.map(
                  (history) => (
                    <div
                      key={
                        history.id
                      }
                      className="p-5 sm:p-6"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <p className="font-semibold text-text-primary">
                          {history.from_status
                            ? `${formatStatus(
                                history.from_status,
                              )} → `
                            : ""}
                          {formatStatus(
                            history.to_status,
                          )}
                        </p>

                        <p className="text-xs text-text-secondary">
                          {formatDate(
                            history.created_at,
                          )}
                        </p>
                      </div>

                      {history.note && (
                        <p className="mt-2 text-sm leading-6 text-text-secondary">
                          {history.note}
                        </p>
                      )}

                      {history.changed_by_name && (
                        <p className="mt-2 text-xs text-text-secondary">
                          Updated by{" "}
                          {
                            history.changed_by_name
                          }
                        </p>
                      )}
                    </div>
                  ),
                )
              ) : (
                <div className="p-6 text-sm text-text-secondary">
                  No status history available.
                </div>
              )}
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

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof UserRound;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-border bg-background p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <Icon className="h-4 w-4" />
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-text-secondary">
            {label}
          </p>

          <p className="mt-2 text-sm font-semibold text-text-primary">
            {value}
          </p>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({
  status,
}: {
  status: ReferralStatus;
}) {
  return (
    <span className="inline-flex w-fit items-center gap-2 border border-gold/30 bg-gold/5 px-4 py-2 text-xs font-bold uppercase tracking-[0.12em] text-gold-deep dark:text-gold">
      <Clock3 className="h-4 w-4" />
      {formatStatus(status)}
    </span>
  );
}
