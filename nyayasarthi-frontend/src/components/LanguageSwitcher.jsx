import { useTranslation } from "react-i18next";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const language = i18n.resolvedLanguage || i18n.language;

  return (
    <label className="sr-only">
      {t("language.select")}
      <select
        aria-label={t("language.select")}
        value={language?.startsWith("hi") ? "hi" : "en"}
        onChange={(event) => i18n.changeLanguage(event.target.value)}
        className="bg-transparent border border-white/20 rounded-md px-2 py-1 text-[11px] text-current"
      >
        <option value="en">English</option>
        <option value="hi">हिन्दी</option>
      </select>
    </label>
  );
}

export default LanguageSwitcher;
