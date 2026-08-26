import {
  AlertCircle,
  Bell,
  Check,
  Clock3,
  Globe2,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Smartphone,
} from "lucide-react";
import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  usePartnerAuth,
} from "../../context/PartnerAuthContext";

import {
  ApiError,
} from "../../services/api";

import {
  getPartnerPreferences,
  getPartnerServices,
  updatePartnerPreferences,
  updatePartnerServices,
} from "../../services/partners";

/* =========================================================
   TYPES
========================================================= */

type SettingsForm = {
  acceptingReferrals: boolean;

  weeklyReferralLimit: string;

  availabilityNote: string;

  emailNotifications: boolean;

  smsNotifications: boolean;

  referralNotifications: boolean;

  verificationNotifications: boolean;

  productUpdates: boolean;

  showPublicPhone: boolean;

  showPublicEmail: boolean;

  allowRemoteReferrals: boolean;
};

const initialSettings: SettingsForm = {
  acceptingReferrals: false,

  weeklyReferralLimit: "",

  availabilityNote: "",

  emailNotifications: true,

  smsNotifications: false,

  referralNotifications: true,

  verificationNotifications: true,

  productUpdates: false,

  showPublicPhone: false,

  showPublicEmail: false,

  allowRemoteReferrals: true,
};

/* =========================================================
   PAGE
========================================================= */

export default function PartnerSettings() {
  const {
    session,
  } = usePartnerAuth();

  const organisationId =
    session?.membership.organisation_id;

  const [
    settings,
    setSettings,
  ] =
    useState<SettingsForm>(
      initialSettings,
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
     LOAD
  ======================================================= */

  useEffect(() => {
    if (!organisationId) {
      setLoading(false);
      return;
    }

    const activeOrganisationId =
      organisationId;

    let active = true;

    async function loadSettings() {
      setLoading(true);
      setError("");

      try {
        const [
          services,
          preferences,
        ] =
          await Promise.all([
            getPartnerServices(
              activeOrganisationId,
            ),

            getPartnerPreferences(
              activeOrganisationId,
            ),
          ]);

        if (!active) {
          return;
        }

        setSettings({
          acceptingReferrals:
            services.accepting_referrals,

          weeklyReferralLimit:
            services.weekly_referral_limit !==
              null
              ? String(
                  services.weekly_referral_limit,
                )
              : "",

          availabilityNote:
            services.availability_note ??
            "",

          emailNotifications:
            preferences.email_notifications,

          smsNotifications:
            preferences.sms_notifications,

          referralNotifications:
            preferences.referral_notifications,

          verificationNotifications:
            preferences.verification_notifications,

          productUpdates:
            preferences.product_updates,

          showPublicPhone:
            preferences.show_public_phone,

          showPublicEmail:
            preferences.show_public_email,

          allowRemoteReferrals:
            preferences.allow_remote_referrals,
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
            "Unable to load partner settings.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadSettings();

    return () => {
      active = false;
    };
  }, [organisationId]);

  /* =======================================================
     CHANGE
  ======================================================= */

  function updateSetting<
    K extends keyof SettingsForm,
  >(
    key: K,
    value: SettingsForm[K],
  ) {
    setSettings(
      (current) => ({
        ...current,
        [key]: value,
      }),
    );

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
      settings.weeklyReferralLimit.trim()
    ) {
      const parsed =
        Number(
          settings.weeklyReferralLimit,
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
      const [
        services,
        preferences,
      ] =
        await Promise.all([
          updatePartnerServices(
            organisationId,
            {
              accepting_referrals:
                settings.acceptingReferrals,

              weekly_referral_limit:
                weeklyReferralLimit,

              availability_note:
                settings.availabilityNote.trim(),
            },
          ),

          updatePartnerPreferences(
            organisationId,
            {
              email_notifications:
                settings.emailNotifications,

              sms_notifications:
                settings.smsNotifications,

              referral_notifications:
                settings.referralNotifications,

              verification_notifications:
                settings.verificationNotifications,

              product_updates:
                settings.productUpdates,

              show_public_phone:
                settings.showPublicPhone,

              show_public_email:
                settings.showPublicEmail,

              allow_remote_referrals:
                settings.allowRemoteReferrals,
            },
          ),
        ]);

      setSettings({
        acceptingReferrals:
          services.accepting_referrals,

        weeklyReferralLimit:
          services.weekly_referral_limit !==
            null
            ? String(
                services.weekly_referral_limit,
              )
            : "",

        availabilityNote:
          services.availability_note,

        emailNotifications:
          preferences.email_notifications,

        smsNotifications:
          preferences.sms_notifications,

        referralNotifications:
          preferences.referral_notifications,

        verificationNotifications:
          preferences.verification_notifications,

        productUpdates:
          preferences.product_updates,

        showPublicPhone:
          preferences.show_public_phone,

        showPublicEmail:
          preferences.show_public_email,

        allowRemoteReferrals:
          preferences.allow_remote_referrals,
      });

      setSaved(true);

      window.setTimeout(
        () => {
          setSaved(false);
        },
        3000,
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
          "Unable to save partner settings.",
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
            Loading partner settings...
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
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
              Partner preferences
            </p>

            <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
              Settings
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Manage referral
              availability,
              notifications, public
              contact preferences and
              operational settings for
              your partner workspace.
            </p>
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

          {/* REFERRAL CAPACITY */}

          <SettingsSection
            icon={SlidersHorizontal}
            eyebrow="Section 01"
            title="Referral capacity"
            description="Control whether your organisation is currently available to receive matched referrals."
          >
            <div className="grid gap-4 lg:grid-cols-[1fr_0.8fr]">
              <ToggleCard
                title="Accepting referrals"
                description="Allow Sauti Yo to consider your organisation for suitable citizen referrals once verification requirements are satisfied."
                checked={
                  settings.acceptingReferrals
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "acceptingReferrals",
                    checked,
                  )
                }
              />

              <div className="border border-border bg-background p-5">
                <label
                  htmlFor="weekly-limit"
                  className="text-sm font-semibold text-text-primary"
                >
                  Weekly referral limit
                </label>

                <p className="mt-2 text-xs leading-5 text-text-secondary">
                  Set an approximate
                  maximum number of new
                  referrals your
                  organisation can
                  reasonably manage each
                  week.
                </p>

                <input
                  id="weekly-limit"
                  type="number"
                  min="0"
                  value={
                    settings.weeklyReferralLimit
                  }
                  onChange={(
                    event,
                  ) =>
                    updateSetting(
                      "weeklyReferralLimit",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. 10"
                  className="mt-4 min-h-12 w-full border border-border bg-surface px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                />
              </div>
            </div>

            <div className="mt-4">
              <label
                htmlFor="availability-note"
                className="text-sm font-semibold text-text-primary"
              >
                Availability note
              </label>

              <textarea
                id="availability-note"
                rows={4}
                value={
                  settings.availabilityNote
                }
                onChange={(
                  event,
                ) =>
                  updateSetting(
                    "availabilityNote",
                    event.target.value,
                  )
                }
                placeholder="e.g. Intake is available Monday to Thursday."
                className="mt-2 w-full resize-y border border-border bg-background px-4 py-3 text-sm leading-6 text-text-primary outline-none transition focus:border-gold"
              />
            </div>
          </SettingsSection>

          {/* NOTIFICATIONS */}

          <SettingsSection
            icon={Bell}
            eyebrow="Section 02"
            title="Notifications"
            description="Choose which partner activity should trigger notifications when notification delivery is enabled."
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <ToggleCard
                icon={Mail}
                title="Email notifications"
                description="Allow partner workspace notifications to be delivered by email."
                checked={
                  settings.emailNotifications
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "emailNotifications",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Smartphone}
                title="SMS notifications"
                description="Allow selected partner notifications to be delivered by SMS."
                checked={
                  settings.smsNotifications
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "smsNotifications",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Clock3}
                title="New referral alerts"
                description="Notify the organisation when a matched referral requires review."
                checked={
                  settings.referralNotifications
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "referralNotifications",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={ShieldCheck}
                title="Verification updates"
                description="Receive updates about verification requests, decisions and requested changes."
                checked={
                  settings.verificationNotifications
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "verificationNotifications",
                    checked,
                  )
                }
              />
            </div>

            <div className="mt-4">
              <ToggleCard
                title="Sauti Yo product updates"
                description="Receive occasional information about partner tools and platform improvements."
                checked={
                  settings.productUpdates
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "productUpdates",
                    checked,
                  )
                }
              />
            </div>
          </SettingsSection>

          {/* CONTACT */}

          <SettingsSection
            icon={Globe2}
            eyebrow="Section 03"
            title="Public contact preferences"
            description="Control which designated support channels may be shown to citizens where appropriate."
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <ToggleCard
                icon={Smartphone}
                title="Show public support phone"
                description="Allow the organisation's designated public support number to be displayed where appropriate."
                checked={
                  settings.showPublicPhone
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "showPublicPhone",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Mail}
                title="Show public support email"
                description="Allow the organisation's designated public support email to be displayed where appropriate."
                checked={
                  settings.showPublicEmail
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "showPublicEmail",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Globe2}
                title="Allow remote referrals"
                description="Permit matching where a citizen prefers online or remote support."
                checked={
                  settings.allowRemoteReferrals
                }
                onChange={(
                  checked,
                ) =>
                  updateSetting(
                    "allowRemoteReferrals",
                    checked,
                  )
                }
              />
            </div>

            <div className="mt-5 flex items-start gap-3 border-l-2 border-gold bg-gold/5 p-4">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

              <p className="text-xs leading-5 text-text-secondary">
                These preferences only
                apply to contact details
                explicitly designated as
                public support channels.
                Administrative or private
                account information should
                never be exposed through
                these settings.
              </p>
            </div>
          </SettingsSection>

          {/* PRIVACY */}

          <SettingsSection
            icon={LockKeyhole}
            eyebrow="Section 04"
            title="Privacy & data handling"
            description="Partner access is restricted to information required to assess and manage authorised referrals."
          >
            <div className="grid gap-4 md:grid-cols-3">
              <PolicyCard
                title="Minimum necessary data"
                text="Partners should receive only the information required to understand and act on a referral."
              />

              <PolicyCard
                title="Citizen consent"
                text="Referral details are shared only through the consent-aware referral workflow."
              />

              <PolicyCard
                title="Access control"
                text="Authenticated partner members are restricted to organisations and referrals they are authorised to access."
              />
            </div>

            <div className="mt-5 border border-border bg-background p-5">
              <p className="text-sm font-semibold text-text-primary">
                Core privacy controls are active.
              </p>

              <p className="mt-2 max-w-3xl text-xs leading-5 text-text-secondary">
                Authentication,
                organisation-scoped
                permissions and referral
                status history are now
                enforced by the backend.
                Additional production
                security hardening should
                still be completed before
                deployment with real
                citizen data.
              </p>
            </div>
          </SettingsSection>

          {/* SECURITY */}

          <SettingsSection
            icon={ShieldCheck}
            eyebrow="Section 05"
            title="Account security"
            description="Partner access is authenticated through the Sauti Yo backend."
          >
            <div className="grid gap-4 md:grid-cols-2">
              <DisabledAction
                title="Change password"
                description="A self-service password management screen has not yet been added to the Partner Portal."
              />

              <DisabledAction
                title="Two-step verification"
                description="Two-step verification is not yet available in the current Partner Portal implementation."
              />
            </div>
          </SettingsSection>

          {/* SAVE */}

          <section className="sticky bottom-0 z-20 mt-6 border border-border bg-surface/95 p-4 shadow-[var(--shadow-soft)] backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {saving
                    ? "Saving settings..."
                    : saved
                      ? "Settings saved"
                      : "Save your partner preferences."}
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  Saved settings are
                  persisted through
                  Django and PostgreSQL.
                </p>
              </div>

              <button
                type="button"
                disabled={saving}
                onClick={
                  handleSave
                }
                className="btn-primary disabled:cursor-not-allowed disabled:opacity-60"
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
                    : "Save Settings"}
              </button>
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

function SettingsSection({
  icon: Icon,
  eyebrow,
  title,
  description,
  children,
}: {
  icon: typeof ShieldCheck;
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

            <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
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

function ToggleCard({
  icon: Icon,
  title,
  description,
  checked,
  onChange,
}: {
  icon?: typeof ShieldCheck;
  title: string;
  description: string;
  checked: boolean;
  onChange: (
    checked: boolean,
  ) => void;
}) {
  return (
    <label
      className={[
        "flex cursor-pointer items-start gap-4 border p-5 transition",

        checked
          ? "border-gold bg-gold/5"
          : "border-border bg-background hover:border-gold/60",
      ].join(" ")}
    >
      {Icon && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
          <Icon className="h-4 w-4" />
        </div>
      )}

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-4">
          <p className="font-semibold text-text-primary">
            {title}
          </p>

          <input
            type="checkbox"
            checked={checked}
            onChange={(
              event,
            ) =>
              onChange(
                event.target.checked,
              )
            }
            className="mt-1 h-4 w-4 shrink-0 accent-[#c99522]"
          />
        </div>

        <p className="mt-2 text-sm leading-6 text-text-secondary">
          {description}
        </p>
      </div>
    </label>
  );
}

function PolicyCard({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="border border-border bg-background p-5">
      <ShieldCheck className="h-5 w-5 text-gold" />

      <p className="mt-4 font-semibold text-text-primary">
        {title}
      </p>

      <p className="mt-2 text-sm leading-6 text-text-secondary">
        {text}
      </p>
    </div>
  );
}

function DisabledAction({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="border border-border bg-background p-5 opacity-75">
      <p className="font-semibold text-text-primary">
        {title}
      </p>

      <p className="mt-2 text-sm leading-6 text-text-secondary">
        {description}
      </p>

      <span className="mt-4 inline-flex border border-border px-3 py-1.5 text-[11px] font-semibold text-text-secondary">
        Not yet available
      </span>
    </div>
  );
}
