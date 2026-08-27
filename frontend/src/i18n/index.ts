import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import lg from "./locales/lg.json";
import sw from "./locales/sw.json";
import nyn from "./locales/nyn.json";

const supportedLanguages = ["en", "lg", "sw", "nyn"];

const savedLanguage =
  typeof window !== "undefined"
    ? window.localStorage.getItem("sauti-yo-language")
    : null;

const initialLanguage =
  savedLanguage && supportedLanguages.includes(savedLanguage)
    ? savedLanguage
    : "en";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    lg: { translation: lg },
    sw: { translation: sw },
    nyn: { translation: nyn },
  },

  lng: initialLanguage,
  fallbackLng: "en",

  interpolation: {
    escapeValue: false,
  },
});

i18n.on("languageChanged", (language) => {
  if (
    typeof window !== "undefined" &&
    supportedLanguages.includes(language)
  ) {
    window.localStorage.setItem(
      "sauti-yo-language",
      language,
    );

    document.documentElement.lang = language;
  }
});

if (typeof document !== "undefined") {
  document.documentElement.lang = initialLanguage;
}

export default i18n;
