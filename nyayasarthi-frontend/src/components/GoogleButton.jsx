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

  // Keep the latest onCredential in a ref, so the effect below never needs
  // it as a dependency — this is what stops re-initialization on every
  // parent render (which was stacking duplicate invisible Google iframes
  // that silently intercepted clicks elsewhere on the page).
  const onCredentialRef = useRef(onCredential);
  useEffect(() => {
    onCredentialRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    if (!clientId || !divRef.current) return;
    let cancelled = false;
    const tryInit = () => {
      if (cancelled) return;
      if (!window.google?.accounts?.id) {
        setTimeout(tryInit, 150);
        return;
      }
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => onCredentialRef.current(response.credential),
      });
      // Clear anything already rendered in this div before rendering again,
      // so repeated calls never stack duplicate button/iframe elements.
      if (divRef.current) divRef.current.innerHTML = "";
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
      if (window.google?.accounts?.id) {
        window.google.accounts.id.cancel();
      }
    };
  }, [clientId]); // ← sirf clientId — language ya onCredential se dobara nahi chalega

  if (!clientId) {
    return (
      <div className="text-xs text-[#8A8371] border border-dashed border-[#DCD5C0] rounded-md px-3 py-2.5 text-center">
        {t("auth.googleNotConfigured")}
      </div>
    );
  }
  return <div ref={divRef} className="flex justify-center" />;
}
