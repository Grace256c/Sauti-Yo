import {
  ArrowRight,
  Headphones,
  Languages,
  MessageSquareText,
  Phone,
  Smartphone,
} from "lucide-react";
import { Link } from "react-router-dom";

import featurePhoneUssd from "../../assets/images/feature-phone-ussd.png";
import smartphoneMockup from "../../assets/images/smartphone-app-mockup.png";

const channels = [
  {
    icon: Smartphone,
    title: "Web",
    text: "Use Sauti Yo on a smartphone, tablet or computer.",
    action: null,
  },
  {
    icon: Phone,
    title: "USSD",
    text: "Use a basic feature phone without mobile data.",
    action: "Dial *384*163024#",
  },
  {
    icon: MessageSquareText,
    title: "SMS",
    text: "Receive concise guidance and follow-up by text.",
    action: "Text 18275",
  },
  {
    icon: Headphones,
    title: "Voice",
    text: "Listen to guidance when reading may be difficult.",
    action: "Call +256 323 200 924",
  },
];

export default function Access() {
  return (
    <>
      <section className="section-padding bg-background">
        <div className="site-container grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Access Sauti Yo
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold text-text-primary sm:text-5xl lg:text-6xl">
              One platform.
              <span className="block text-gold-deep dark:text-gold">
                Different ways to reach it.
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary sm:text-lg">
              Access should adapt to the user’s device, connectivity and
              accessibility needs.
            </p>

            <Link to="/rights" className="btn-primary mt-8">
              Start Here
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="image-frame">
            <img
              src={smartphoneMockup}
              alt="Sauti Yo smartphone experience"
              className="image-soften w-full object-cover"
            />
          </div>
        </div>
      </section>

      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {channels.map((channel) => {
              const Icon = channel.icon;

              return (
                <article key={channel.title} className="card-surface p-6">
                  <Icon className="h-6 w-6 text-gold" />
                  <h2 className="mt-5 text-xl font-semibold text-text-primary">
                    {channel.title}
                  </h2>
                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {channel.text}
                  </p>
                  {channel.action && (
                    <p className="mt-4 text-sm font-bold text-gold-deep dark:text-gold">
                      {channel.action}
                    </p>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="section-padding bg-background">
        <div className="site-container grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div className="image-frame">
            <img
              src={featurePhoneUssd}
              alt="Sauti Yo feature phone access"
              className="image-soften w-full object-cover"
            />
          </div>

          <div>
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Feature-phone access
              </p>
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
              No smartphone?
              <span className="block text-gold-deep dark:text-gold">
                You can still begin.
              </span>
            </h2>

            <p className="mt-6 text-base leading-7 text-text-secondary">
              USSD allows a simplified Rights-to-Action experience without
              requiring an app or mobile data.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <p className="border border-gold bg-gold/10 px-4 py-3 text-sm font-bold text-gold-deep dark:text-gold">
                Dial *384*163024#
              </p>

              <p className="border border-border bg-surface px-4 py-3 text-sm font-bold text-text-primary">
                Text 18275
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-surface-soft">
        <div className="site-container grid gap-10 lg:grid-cols-2">
          <div>
            <Languages className="h-7 w-7 text-gold" />
            <h2 className="heading-serif mt-5 text-3xl font-semibold text-text-primary sm:text-4xl">
              Language access matters.
            </h2>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {["English", "Luganda", "Kiswahili", "Runyankole"].map(
              (language) => (
                <div
                  key={language}
                  className="border border-border bg-surface px-4 py-4 text-sm font-medium text-text-primary"
                >
                  {language}
                </div>
              ),
            )}
          </div>
        </div>
      </section>
    </>
  );
}
