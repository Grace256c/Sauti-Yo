import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Inbox,
  LoaderCircle,
  Search,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ApiError,
} from "../../services/api";

import {
  getReferrals,
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

type ReferralItem = {
  id: number;
  reference: string;
  category: string;
  supportType: string;
  district: string;
  language: string;
  preferredChannel: string;
  status: ReferralStatus;
  createdAt: string;
  summary: string;
};

/* =========================================================
   OPTIONS
========================================================= */

const statusOptions: {
  value:
    | "all"
    | ReferralStatus;
  label: string;
}[] = [
  {
    value: "all",
    label: "All referrals",
  },
  {
    value: "new",
    label: "New",
  },
  {
    value: "reviewing",
    label: "Reviewing",
  },
  {
    value: "accepted",
    label: "Accepted",
  },
  {
    value: "in_progress",
    label: "In progress",
  },
  {
    value: "completed",
    label: "Completed",
  },
  {
    value: "closed",
    label: "Closed",
  },
];

/* =========================================================
   HELPERS
========================================================= */

function normalizeStatus(
  status: string,
): ReferralStatus {
  switch (status) {
    case "reviewing":
      return "reviewing";

    case "accepted":
      return "accepted";

    case "in_progress":
    case "in-progress":
      return "in_progress";

    case "completed":
      return "completed";

    case "closed":
      return "closed";

    default:
      return "new";
  }
}

function formatDate(
  value?: string,
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

function referralToItem(
  referral: Referral,
): ReferralItem {
  return {
    id: referral.id,

    reference:
      referral.reference,

    /*
     * The current referral serializer exposes rights_topic
     * as an ID rather than a nested topic title.
     *
     * Until we expand that serializer, this keeps the UI
     * truthful rather than inventing category names.
     */
    category:
      referral.rights_topic
        ? `Rights topic #${referral.rights_topic}`
        : "General support",

    supportType:
      referral.preferred_support_channel
        ? "Matched support"
        : "General support",

    district:
      referral.district ||
      "District not specified",

    language:
      referral.language ||
      "Language not specified",

    preferredChannel:
      referral.preferred_support_channel ||
      "Channel not specified",

    status:
      normalizeStatus(
        referral.status,
      ),

    createdAt:
      formatDate(
        referral.created_at,
      ),

    summary:
      referral.summary ||
      "No referral summary provided.",
  };
}

/* =========================================================
   PAGE
========================================================= */

export default function PartnerReferrals() {
  const [
    referrals,
    setReferrals,
  ] =
    useState<ReferralItem[]>(
      [],
    );

  const [
    search,
    setSearch,
  ] =
    useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] =
    useState<
      "all" | ReferralStatus
    >(
      "all",
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
     LOAD FROM DJANGO
  ======================================================= */

  useEffect(() => {
    let active = true;

    async function loadReferrals() {
      setLoading(true);
      setError("");

      try {
        const data =
          await getReferrals();

        if (!active) {
          return;
        }

        setReferrals(
          data.map(
            referralToItem,
          ),
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
            "Unable to load referrals.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadReferrals();

    return () => {
      active = false;
    };
  }, []);

  /* =======================================================
     FILTERING
  ======================================================= */

  const filteredReferrals =
    useMemo(() => {
      const query =
        search
          .trim()
          .toLowerCase();

      return referrals.filter(
        (referral) => {
          const matchesStatus =
            statusFilter ===
              "all" ||
            referral.status ===
              statusFilter;

          const matchesSearch =
            query === "" ||
            referral.reference
              .toLowerCase()
              .includes(query) ||
            referral.category
              .toLowerCase()
              .includes(query) ||
            referral.supportType
              .toLowerCase()
              .includes(query) ||
            referral.district
              .toLowerCase()
              .includes(query) ||
            referral.language
              .toLowerCase()
              .includes(query);

          return (
            matchesStatus &&
            matchesSearch
          );
        },
      );
    }, [
      referrals,
      search,
      statusFilter,
    ]);

  /* =======================================================
     COUNTS
  ======================================================= */

  const counts =
    useMemo(() => {
      return {
        new:
          referrals.filter(
            (item) =>
              item.status ===
              "new",
          ).length,

        reviewing:
          referrals.filter(
            (item) =>
              item.status ===
              "reviewing",
          ).length,

        active:
          referrals.filter(
            (item) =>
              item.status ===
                "accepted" ||
              item.status ===
                "in_progress",
          ).length,

        completed:
          referrals.filter(
            (item) =>
              item.status ===
              "completed",
          ).length,
      };
    }, [referrals]);

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center px-5">
        <div className="text-center">
          <LoaderCircle className="mx-auto h-6 w-6 animate-spin text-gold" />

          <p className="mt-4 text-sm text-text-secondary">
            Loading referrals...
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
                Referral management
              </p>

              <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                Referrals
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                Review matched citizen
                referrals, decide whether
                your organisation can
                assist and track active
                support through to
                completion.
              </p>
            </div>

            <div className="inline-flex w-fit items-center gap-2 border border-border bg-background px-4 py-2.5 text-sm">
              <ShieldCheck className="h-4 w-4 text-gold" />

              <span className="font-semibold text-text-primary">
                Partner referral workspace
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          BODY
      ===================================================== */}

      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-7xl">

          {/* ERROR */}

          {error && (
            <div className="mb-5 flex items-start gap-3 border border-danger/30 bg-danger/5 p-4">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-danger" />

              <p className="text-sm leading-6 text-danger">
                {error}
              </p>
            </div>
          )}

          {/* =================================================
              REFERRAL SAFETY NOTE
          ================================================= */}

          <section className="border border-border bg-surface p-5 sm:p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                <ShieldCheck
                  className="h-5 w-5"
                  strokeWidth={1.7}
                />
              </div>

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Referral privacy
                </p>

                <h2 className="mt-2 text-lg font-semibold text-text-primary">
                  Only information the
                  citizen agreed to share
                  should appear here.
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
                  A match does not give a
                  partner unrestricted
                  access to a citizen's
                  full journey. Referral
                  records should contain
                  only information needed
                  to assess and provide
                  the requested support.
                </p>
              </div>
            </div>
          </section>

          {/* =================================================
              SUMMARY
          ================================================= */}

          <section className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <ReferralStat
              label="New"
              value={counts.new}
              icon={Inbox}
              description="Awaiting review"
            />

            <ReferralStat
              label="Reviewing"
              value={
                counts.reviewing
              }
              icon={Search}
              description="Under assessment"
            />

            <ReferralStat
              label="Active"
              value={counts.active}
              icon={Clock3}
              description="Accepted / in progress"
            />

            <ReferralStat
              label="Completed"
              value={
                counts.completed
              }
              icon={CheckCircle2}
              description="Support completed"
            />
          </section>

          {/* =================================================
              FILTERS
          ================================================= */}

          <section className="mt-5 border border-border bg-surface">
            <div className="grid gap-4 p-5 md:grid-cols-[1fr_auto] md:items-center sm:p-6">
              <div className="relative">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />

                <input
                  type="search"
                  value={search}
                  onChange={(
                    event,
                  ) =>
                    setSearch(
                      event.target
                        .value,
                    )
                  }
                  placeholder="Search by reference, category, support type, district or language"
                  className="min-h-12 w-full border border-border bg-background pl-11 pr-4 text-sm text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
                />
              </div>

              <select
                value={
                  statusFilter
                }
                onChange={(
                  event,
                ) =>
                  setStatusFilter(
                    event.target
                      .value as
                      | "all"
                      | ReferralStatus,
                  )
                }
                className="min-h-12 min-w-[180px] border border-border bg-background px-4 text-sm text-text-primary outline-none transition focus:border-gold"
              >
                {statusOptions.map(
                  (option) => (
                    <option
                      key={
                        option.value
                      }
                      value={
                        option.value
                      }
                    >
                      {
                        option.label
                      }
                    </option>
                  ),
                )}
              </select>
            </div>
          </section>

          {/* =================================================
              REFERRAL INBOX
          ================================================= */}

          <section className="mt-5 border border-border bg-surface">
            <div className="flex flex-col gap-3 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Referral inbox
                </p>

                <h2 className="heading-serif mt-2 text-2xl font-semibold text-text-primary">
                  Citizen referrals
                </h2>
              </div>

              <p className="text-xs font-semibold text-text-secondary">
                {
                  filteredReferrals.length
                }{" "}
                shown
              </p>
            </div>

            {filteredReferrals.length >
            0 ? (
              <div className="divide-y divide-border">
                {filteredReferrals.map(
                  (referral) => (
                    <ReferralRow
                      key={
                        referral.id
                      }
                      referral={
                        referral
                      }
                    />
                  ),
                )}
              </div>
            ) : (
              <EmptyReferralState
                hasFilters={
                  search.trim() !== "" ||
                  statusFilter !==
                    "all"
                }
              />
            )}
          </section>

          {/* =================================================
              REFERRAL FLOW
          ================================================= */}

          <section className="mt-5 border border-border bg-surface">
            <div className="grid gap-8 p-6 sm:p-7 lg:grid-cols-[0.75fr_1.25fr] lg:items-center">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Referral workflow
                </p>

                <h2 className="heading-serif mt-3 text-2xl font-semibold leading-tight text-text-primary sm:text-3xl">
                  A referral should move
                  through clear,
                  accountable stages.
                </h2>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <WorkflowStep
                  number="01"
                  title="Review"
                  text="Check whether the referral fits your organisation's services and capacity."
                />

                <WorkflowStep
                  number="02"
                  title="Respond"
                  text="Accept or decline promptly so the citizen is not left waiting unnecessarily."
                />

                <WorkflowStep
                  number="03"
                  title="Update"
                  text="Keep referral status current while support is in progress and when it is completed."
                />
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

function ReferralStat({
  label,
  value,
  icon: Icon,
  description,
}: {
  label: string;
  value: number;
  icon: typeof Inbox;
  description: string;
}) {
  return (
    <div className="border border-border bg-surface px-5 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-text-secondary">
            {label}
          </p>

          <p className="mt-2 text-xl font-semibold text-text-primary">
            {value}
          </p>

          <p className="mt-1 text-xs text-text-secondary">
            {description}
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

function ReferralRow({
  referral,
}: {
  referral: ReferralItem;
}) {
  return (
    <article className="group p-5 transition hover:bg-background sm:p-6">
      <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
            <UserRound
              className="h-5 w-5"
              strokeWidth={1.7}
            />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-semibold text-text-primary">
                {
                  referral.reference
                }
              </p>

              <ReferralStatusBadge
                status={
                  referral.status
                }
              />
            </div>

            <p className="mt-2 font-semibold text-text-primary">
              {referral.category}
            </p>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
              {referral.summary}
            </p>

            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-text-secondary">
              <span>
                {
                  referral.supportType
                }
              </span>

              <span>
                {
                  referral.district
                }
              </span>

              <span>
                {
                  referral.language
                }
              </span>

              <span>
                {
                  referral.preferredChannel
                }
              </span>

              <span>
                {
                  referral.createdAt
                }
              </span>
            </div>
          </div>
        </div>

        <a
          href={`/partner/referrals/${referral.id}`}
          className="inline-flex min-h-11 items-center justify-center gap-2 border border-border px-4 text-sm font-semibold text-text-primary transition hover:border-gold hover:text-gold"
        >
          Review referral

          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </a>
      </div>
    </article>
  );
}

function ReferralStatusBadge({
  status,
}: {
  status: ReferralStatus;
}) {
  const labels: Record<
    ReferralStatus,
    string
  > = {
    new: "New",
    reviewing: "Reviewing",
    accepted: "Accepted",
    in_progress:
      "In progress",
    completed: "Completed",
    closed: "Closed",
  };

  return (
    <span className="inline-flex border border-gold/30 bg-gold/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-gold-deep dark:text-gold">
      {labels[status]}
    </span>
  );
}

function EmptyReferralState({
  hasFilters,
}: {
  hasFilters: boolean;
}) {
  return (
    <div className="flex min-h-[390px] items-center justify-center p-7">
      <div className="max-w-md text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gold/10 text-gold">
          {hasFilters ? (
            <Search
              className="h-6 w-6"
              strokeWidth={1.7}
            />
          ) : (
            <Inbox
              className="h-6 w-6"
              strokeWidth={1.7}
            />
          )}
        </div>

        <h3 className="heading-serif mt-5 text-2xl font-semibold text-text-primary">
          {hasFilters
            ? "No referrals match these filters."
            : "No referrals yet."}
        </h3>

        <p className="mt-3 text-sm leading-6 text-text-secondary">
          {hasFilters
            ? "Try changing the search term or referral status filter."
            : "Once your organisation is verified, accepting referrals and matched with a citizen request, new referrals will appear here."}
        </p>

        {!hasFilters && (
          <div className="mt-6 flex items-start gap-3 border border-border bg-background p-4 text-left">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

            <p className="text-xs leading-5 text-text-secondary">
              Only real referrals
              returned by the Sauti Yo
              backend appear in this
              inbox. The portal does not
              generate sample citizen
              cases automatically.
            </p>
          </div>
        )}
      </div>
    </div>
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
