import {
  Bell,
  Check,
  Clock3,
  Globe2,
  LockKeyhole,
  Mail,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Smartphone,
} from "lucide-react";
import { useState } from "react";

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

export default function PartnerSettings() {
  const [settings, setSettings] =
    useState<SettingsForm>(() => {
      try {
        const stored =
          sessionStorage.getItem(
            "sauti-yo-partner-settings-draft",
          );

        return stored
          ? (JSON.parse(
              stored,
            ) as SettingsForm)
          : initialSettings;
      } catch {
        return initialSettings;
      }
    });

  const [saved, setSaved] =
    useState(false);

  const updateSetting = <
    K extends keyof SettingsForm,
  >(
    key: K,
    value: SettingsForm[K],
  ) => {
    setSettings((current) => ({
      ...current,
      [key]: value,
    }));

    setSaved(false);
  };

  const handleSave = () => {
    sessionStorage.setItem(
      "sauti-yo-partner-settings-draft",
      JSON.stringify(settings),
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
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
              Partner preferences
            </p>

            <h1 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
              Settings
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Manage referral availability,
              notifications, privacy preferences and
              operational settings for your partner
              workspace.
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          BODY
      ===================================================== */}
      <div className="px-5 py-7 sm:px-8 lg:px-10 lg:py-8 xl:px-12">
        <div className="mx-auto max-w-6xl">
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
                description="Allow Sauti Yo to consider your organisation for suitable citizen referrals once verification is complete."
                checked={
                  settings.acceptingReferrals
                }
                onChange={(checked) =>
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
                  Suggested weekly referral limit
                </label>

                <p className="mt-2 text-xs leading-5 text-text-secondary">
                  This can later help prevent the
                  organisation from receiving more
                  new referrals than it can manage.
                </p>

                <input
                  id="weekly-limit"
                  type="number"
                  min="0"
                  value={
                    settings.weeklyReferralLimit
                  }
                  onChange={(event) =>
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
                onChange={(event) =>
                  updateSetting(
                    "availabilityNote",
                    event.target.value,
                  )
                }
                placeholder="e.g. Intake is available Monday to Thursday. Urgent protection cases are reviewed separately."
                className="mt-2 w-full resize-y border border-border bg-background px-4 py-3 text-sm leading-6 text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
              />
            </div>
          </SettingsSection>

          {/* NOTIFICATIONS */}
          <SettingsSection
            icon={Bell}
            eyebrow="Section 02"
            title="Notifications"
            description="Choose which partner activity should trigger notifications."
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <ToggleCard
                icon={Mail}
                title="Email notifications"
                description="Receive partner workspace notifications by email."
                checked={
                  settings.emailNotifications
                }
                onChange={(checked) =>
                  updateSetting(
                    "emailNotifications",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Smartphone}
                title="SMS notifications"
                description="Receive selected partner notifications by SMS."
                checked={
                  settings.smsNotifications
                }
                onChange={(checked) =>
                  updateSetting(
                    "smsNotifications",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Clock3}
                title="New referral alerts"
                description="Notify the organisation when a new matched referral requires review."
                checked={
                  settings.referralNotifications
                }
                onChange={(checked) =>
                  updateSetting(
                    "referralNotifications",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={ShieldCheck}
                title="Verification updates"
                description="Receive updates about verification requests, decisions or required changes."
                checked={
                  settings.verificationNotifications
                }
                onChange={(checked) =>
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
                description="Receive occasional updates about partner tools, service improvements and new platform features."
                checked={
                  settings.productUpdates
                }
                onChange={(checked) =>
                  updateSetting(
                    "productUpdates",
                    checked,
                  )
                }
              />
            </div>
          </SettingsSection>

          {/* PUBLIC CONTACT */}
          <SettingsSection
            icon={Globe2}
            eyebrow="Section 03"
            title="Public contact preferences"
            description="Control which approved contact channels may later appear to referred citizens."
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <ToggleCard
                icon={Smartphone}
                title="Show public support phone"
                description="Allow the organisation's designated public support number to be shown where appropriate."
                checked={
                  settings.showPublicPhone
                }
                onChange={(checked) =>
                  updateSetting(
                    "showPublicPhone",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Mail}
                title="Show public support email"
                description="Allow the organisation's designated public support email to be shown where appropriate."
                checked={
                  settings.showPublicEmail
                }
                onChange={(checked) =>
                  updateSetting(
                    "showPublicEmail",
                    checked,
                  )
                }
              />

              <ToggleCard
                icon={Globe2}
                title="Allow remote referrals"
                description="Include your organisation in matching where a citizen prefers online or remote support."
                checked={
                  settings.allowRemoteReferrals
                }
                onChange={(checked) =>
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
                These settings should never make
                private administrative contact
                details public. Only contact details
                specifically designated for citizen
                support should be eligible for
                display.
              </p>
            </div>
          </SettingsSection>

          {/* PRIVACY */}
          <SettingsSection
            icon={LockKeyhole}
            eyebrow="Section 04"
            title="Privacy & data handling"
            description="Partner access should remain limited to information required to assess and manage referrals."
          >
            <div className="grid gap-4 md:grid-cols-3">
              <PolicyCard
                title="Minimum necessary data"
                text="Partners should receive only the information required to understand and act on a referral."
              />

              <PolicyCard
                title="Citizen consent"
                text="Identifiable citizen information should only be shared after appropriate consent."
              />

              <PolicyCard
                title="Access control"
                text="Partner team members should only access referral information appropriate to their role."
              />
            </div>

            <div className="mt-5 border border-border bg-background p-5">
              <p className="text-sm font-semibold text-text-primary">
                Privacy controls are not fully active yet.
              </p>

              <p className="mt-2 max-w-3xl text-xs leading-5 text-text-secondary">
                Authentication, permissions, audit
                logging and secure referral data
                handling should be implemented in the
                backend before real citizen
                information is processed.
              </p>
            </div>
          </SettingsSection>

          {/* ACCOUNT SECURITY */}
          <SettingsSection
            icon={ShieldCheck}
            eyebrow="Section 05"
            title="Account security"
            description="Security settings will become available once partner authentication is connected."
          >
            <div className="grid gap-4 md:grid-cols-2">
              <DisabledAction
                title="Change password"
                description="Password management will be handled through the authenticated partner account."
              />

              <DisabledAction
                title="Two-step verification"
                description="Additional account protection can be enabled when authentication is implemented."
              />
            </div>
          </SettingsSection>

          {/* SAVE BAR */}
          <section className="sticky bottom-0 z-20 mt-6 border border-border bg-surface/95 p-4 shadow-[var(--shadow-soft)] backdrop-blur sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {saved
                    ? "Settings saved"
                    : "Save your partner preferences."}
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  This prototype stores settings only
                  in the current browser session.
                </p>
              </div>

              <button
                type="button"
                onClick={handleSave}
                className="btn-primary"
              >
                {saved ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Save className="h-4 w-4" />
                )}

                {saved
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
  onChange: (checked: boolean) => void;
}) {
  return (
    <label
      className={[
        "flex min-h-[150px] cursor-pointer flex-col border p-5 transition",

        checked
          ? "border-gold bg-gold/5"
          : "border-border bg-background hover:border-gold/60",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          {Icon && (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
              <Icon
                className="h-4 w-4"
                strokeWidth={1.7}
              />
            </div>
          )}

          <p className="font-semibold text-text-primary">
            {title}
          </p>
        </div>

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

function PolicyCard({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="border-t border-border pt-4">
      <p className="font-semibold text-text-primary">
        {title}
      </p>

      <p className="mt-2 text-xs leading-5 text-text-secondary">
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
    <div className="border border-border bg-background p-5">
      <div className="flex items-start gap-3">
        <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-text-secondary" />

        <div>
          <h3 className="font-semibold text-text-primary">
            {title}
          </h3>

          <p className="mt-2 text-sm leading-6 text-text-secondary">
            {description}
          </p>

          <span className="mt-4 inline-flex border border-border px-3 py-1.5 text-[11px] font-semibold text-text-secondary">
            Available after authentication
          </span>
        </div>
      </div>
    </div>
  );
}