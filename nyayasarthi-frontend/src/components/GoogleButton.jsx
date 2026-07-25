import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

/**
 * Renders Google's own "Sign in with Google" button via Google Identity
 * Services (loaded as a <script> tag in index.html — no npm package needed).
 * On success it hands the raw ID token credential up to the caller, which
 * POSTs it to /api/v1/auth/google for verification. This component never
 * sees or trusts anything about the user itself — Google's client library
 * and our backend do all the real verification.
 */
export default function GoogleButton({ onCredential }) {
  const { t, i18n } = useTranslation();
  const divRef = useRef(null);
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId || !divRef.current) return;

    // The GSI script loads async — wait for it if it hasn't attached yet.
    let cancelled = false;
    const tryInit = () => {
      if (cancelled) return;
      if (!window.google?.accounts?.id) {
        setTimeout(tryInit, 150);
        return;
      }
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => onCredential(response.credential),
      });
      window.google.accounts.id.renderButton(divRef.current, {
        theme: "outline",
        size: "large",
        width: 320,
        text: "continue_with",
      });
    };
    tryInit();
    return () => {
      cancelled = true;
    };
  }, [clientId, onCredential, i18n.language]);

  if (!clientId) {
    return (
      <div className="text-xs text-[#8A8371] border border-dashed border-[#DCD5C0] rounded-md px-3 py-2.5 text-center">
        {t("auth.googleNotConfigured")}
      </div>
    );
  }

  return <div ref={divRef} className="flex justify-center" />;
}
