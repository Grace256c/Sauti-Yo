import {
  ArrowRight,
  CheckCircle2,
  Headphones,
  Languages,
  MessageSquareText,
  Phone,
  Smartphone,
  WifiOff,
} from "lucide-react";
import { Link } from "react-router-dom";

import featurePhoneUssd from "../../assets/images/feature-phone-ussd.png";
import smartphoneMockup from "../../assets/images/smartphone-app-mockup.png";
import legalBackground from "../../assets/images/legal-background.png";

const channels = [
  {
    icon: Smartphone,
    title: "Web",
    text: "Use Sauti Yo on a smartphone, tablet or computer for the richest experience.",
    note: "Best for connected devices",
  },
  {
    icon: Phone,
    title: "USSD",
    text: "Access guided rights information from a basic phone without mobile data.",
    note: "Designed for feature phones",
  },
  {
    icon: MessageSquareText,
    title: "SMS",
    text: "Receive short guidance, reminders and follow-up information by text message.",
    note: "Useful for simple follow-up",
  },
  {
    icon: Headphones,
    title: "Voice",
    text: "Listen to spoken guidance where reading may be difficult or inconvenient.",
    note: "Supports accessibility",
  },
];

const principles = [
  "No smartphone should be required to begin.",
  "Low connectivity should not automatically block access.",
  "The same core guidance should remain consistent across channels.",
  "Language and accessibility needs should shape how information is delivered.",
];

export default function Access() {
  return (
    <>
      {/* HERO */}
      <section className="relative isolate overflow-hidden bg-background">
        <img
          src={legalBackground}
          alt=""
          aria-hidden="true"
          className="legal-image absolute inset-0 -z-20 h-full w-full object-cover object-[72%_center]"
        />

        <div className="legal-overlay-light absolute inset-0 -z-10" />

        <div className="site-container py-20 sm:py-24 lg:py-32">
          <div className="grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
            <div className="max-w-2xl animate-fade-up">
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Access Sauti Yo
                </p>
              </div>

              <h1 className="heading-serif text-balance text-4xl font-semibold leading-[1.05] text-text-primary sm:text-5xl lg:text-6xl">
                One platform.
                <span className="block text-gold-deep dark:text-gold">
                  Different ways to reach it.
                </span>
              </h1>

              <p className="mt-7 max-w-xl text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
                Sauti Yo is designed to remain useful across different
                devices, connectivity levels and accessibility needs.
              </p>

              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3">
                {[
                  "Web access",
                  "Feature-phone access",
                  "Voice and text options",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 text-sm text-text-secondary"
                  >
                    <CheckCircle2 className="h-4 w-4 text-gold" />
                    {item}
                  </div>
                ))}
              </div>

              <Link to="/rights" className="btn-primary mt-8">
                Start with Your Situation
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="image-frame">
              <img
                src={smartphoneMockup}
                alt="Sauti Yo smartphone interface"
                className="image-soften w-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* CHANNELS */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-4 flex items-center justify-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Access channels
              </p>

              <span className="gold-rule" />
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
              Choose the channel that works for you
            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-text-secondary">
              The goal is not to force everyone into the same device or
              interface. The goal is to keep the core guidance
              accessible.
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {channels.map((channel) => {
              const Icon = channel.icon;

              return (
                <article
                  key={channel.title}
                  className="card-surface p-6 sm:p-7"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                    <Icon className="h-5 w-5" strokeWidth={1.7} />
                  </div>

                  <h3 className="mt-5 text-xl font-semibold text-text-primary">
                    {channel.title}
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {channel.text}
                  </p>

                  <p className="mt-5 text-xs font-semibold uppercase tracking-[0.13em] text-gold-deep dark:text-gold">
                    {channel.note}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* FEATURE PHONE */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <div className="image-frame">
              <img
                src={featurePhoneUssd}
                alt="Sauti Yo on a feature phone"
                className="image-soften h-full w-full object-cover"
              />
            </div>

            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Built for real connectivity conditions
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                No smartphone?
                <span className="block text-gold-deep dark:text-gold">
                  You can still begin.
                </span>
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                USSD gives people a way to move through a simplified
                Rights-to-Action journey using a basic feature phone.
              </p>

              <div className="mt-8 space-y-4">
                {[
                  "No app installation required",
                  "No mobile data required for USSD access",
                  "Simple menu-based navigation",
                  "Core rights guidance remains consistent",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                    <p className="text-sm leading-6 text-text-secondary">
                      {item}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ACCESS PRINCIPLES */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Accessibility principles
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
                Access is part of the product,
                <span className="block text-gold-deep dark:text-gold">
                  not an afterthought.
                </span>
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                Sauti Yo should work for people with different devices,
                literacy levels, language preferences and connectivity
                conditions.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {principles.map((principle, index) => (
                <div
                  key={principle}
                  className="card-surface p-5 sm:p-6"
                >
                  <span className="text-xs font-bold text-gold">
                    0{index + 1}
                  </span>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {principle}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* OFFLINE / LOW CONNECTIVITY */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid gap-10 lg:grid-cols-[0.7fr_1.3fr] lg:items-center lg:gap-16">
            <div className="flex justify-center">
              <div className="flex h-28 w-28 items-center justify-center rounded-full border border-gold bg-gold/10 text-gold">
                <WifiOff className="h-12 w-12" strokeWidth={1.5} />
              </div>
            </div>

            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Low connectivity
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl">
                Connectivity should shape the experience,
                <span className="block text-gold-deep dark:text-gold">
                  not determine whether access exists.
                </span>
              </h2>

              <p className="mt-6 max-w-2xl text-base leading-7 text-text-secondary">
                Different channels allow Sauti Yo to adapt the amount of
                information, interaction style and media to the user's
                connection and device.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* LANGUAGE */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid items-center gap-10 lg:grid-cols-[1fr_0.8fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Language access
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
                Rights information should be understandable,
                <span className="block text-gold-deep dark:text-gold">
                  not merely available.
                </span>
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                The interface is being structured to support multiple
                languages so users can engage with guidance in a form
                that is easier to understand.
              </p>
            </div>

            <div className="card-surface p-6 sm:p-8">
              <Languages className="h-7 w-7 text-gold" strokeWidth={1.6} />

              <p className="mt-5 text-xs font-bold uppercase tracking-[0.15em] text-gold-deep dark:text-gold">
                Languages
              </p>

              <div className="mt-5 grid grid-cols-2 gap-3">
                {["English", "Luganda", "Kiswahili", "Runyankole"].map(
                  (language) => (
                    <div
                      key={language}
                      className="border border-border bg-background px-4 py-3 text-sm font-medium text-text-primary"
                    >
                      {language}
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-[#191919] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Ready to begin?
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold sm:text-4xl lg:text-5xl">
                Use the channel that works for you.
                <span className="block text-gold">
                  The journey starts with your situation.
                </span>
              </h2>
            </div>

            <Link
              to="/rights"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition hover:bg-transparent hover:text-gold sm:w-auto"
            >
              Start Here
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}