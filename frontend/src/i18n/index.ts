import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import lg from "./locales/lg.json";
import sw from "./locales/sw.json";
import nyn from "./locales/nyn.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    lg: { translation: lg },
    sw: { translation: sw },
    nyn: { translation: nyn },
  },

  // Web is intentionally English-only for this MVP.
  lng: "en",
  fallbackLng: "en",

  interpolation: {
    escapeValue: false,
  },
});

if (typeof document !== "undefined") {
  document.documentElement.lang = "en";
}

export default i18n;
