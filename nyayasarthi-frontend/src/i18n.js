import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import en from "./locales/en/common.json";
import hi from "./locales/hi/common.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { common: en }, hi: { common: hi } },
    fallbackLng: "en",
    supportedLngs: ["en", "hi"],
    ns: ["common"],
    defaultNS: "common",
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: "nyayasarthi_language",
      caches: ["localStorage"],
    },
  });

export default i18n;
