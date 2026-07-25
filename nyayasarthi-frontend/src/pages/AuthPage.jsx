import React, { useEffect, useState } from "react";
import { AlertTriangle, Loader2, Scale, ShieldCheck } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import GoogleButton from "../components/GoogleButton";
import * as api from "../api";
import { useTranslation } from "react-i18next";

const ROLES = [
  { value: "department_officer", key: "roles.department_officer" },
  { value: "legal_officer", key: "roles.legal_officer", needsInvite: true },
  { value: "admin_authority", key: "roles.admin_authority", needsInvite: true },
  { value: "auditor", key: "roles.auditorReadOnly", needsInvite: true },
];

const emptyForm = { full_name: "", email: "", password: "", role: "department_officer", department_id: "", invite_code: "" };

export default function AuthPage() {
  const { login, signup, loginWithGoogle } = useAuth();
  const { t } = useTranslation();
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .listDepartments()
      .then((res) => setDepartments(res.data))
      .catch(() => {});
  }, []);

  function switchMode(next) {
    setMode(next);
    setError("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") {
        await login(form.email.trim(), form.password);
      } else {
        await signup({ ...form, email: form.email.trim(), department_id: form.department_id || null });
      }
    } catch (err) {
      setError(err?.response?.data?.detail || t("auth.genericError"));
    } finally {
      setBusy(false);
    }
  }

  async function handleGoogle(credential) {
    setError("");
    setBusy(true);
    try {
      await loginWithGoogle(credential);
    } catch (err) {
      setError(err?.response?.data?.detail || t("auth.googleError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2.5 justify-center mb-7">
          <div className="w-9 h-9 rounded-lg bg-gold flex items-center justify-center">
            <Scale size={18} className="text-navy" />
          </div>
          <div>
            <div className="font-serif text-xl font-bold leading-none text-navy">{t("brand.name")}</div>
            <div className="text-[10px] text-[#8A8371] tracking-wide mt-0.5">{t("brand.tagline")}</div>
          </div>
        </div>

        <div className="bg-white border border-[#E7E1D3] rounded-2xl p-7">
          <div className="flex gap-1 mb-6 bg-paper rounded-lg p-1">
            <button
              type="button"
              onClick={() => switchMode("login")}
              className={`flex-1 text-sm font-semibold py-2 rounded-md transition-colors ${
                mode === "login" ? "bg-navy text-white" : "text-[#6B7280]"
              }`}
            >
              {t("auth.login")}
            </button>
            <button
              type="button"
              onClick={() => switchMode("signup")}
              className={`flex-1 text-sm font-semibold py-2 rounded-md transition-colors ${
                mode === "signup" ? "bg-navy text-white" : "text-[#6B7280]"
              }`}
            >
              {t("auth.createAccount")}
            </button>
          </div>

          <div className="mb-5">
            <GoogleButton onCredential={handleGoogle} />
          </div>
          <div className="flex items-center gap-3 mb-5">
            <div className="h-px bg-[#E7E1D3] flex-1" />
            <div className="text-[11px] text-[#8A8371] uppercase tracking-wide">{t("auth.officialEmail")}</div>
            <div className="h-px bg-[#E7E1D3] flex-1" />
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
            {mode === "signup" && (
              <Field label={t("auth.fullName")}>
                <input
                  required
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="border border-[#DCD5C0] rounded-md px-3 py-2 text-sm w-full"
                  placeholder={t("auth.namePlaceholder")}
                />
              </Field>
            )}

            <Field label={t("auth.email")}>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="border border-[#DCD5C0] rounded-md px-3 py-2 text-sm w-full"
                placeholder={t("auth.emailPlaceholder")}
              />
            </Field>

            <Field label={t("auth.password")}>
              <input
                required
                type="password"
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="border border-[#DCD5C0] rounded-md px-3 py-2 text-sm w-full"
                placeholder={mode === "signup" ? t("auth.passwordHint") : "••••••••"}
              />
            </Field>

            {mode === "signup" && (
              <>
                <Field label={t("auth.role")}>
                  <select
                    value={form.role}
                    onChange={(e) => setForm({ ...form, role: e.target.value })}
                    className="border border-[#DCD5C0] rounded-md px-3 py-2 text-sm w-full bg-white"
                  >
                    {ROLES.map((r) => (
                      <option key={r.value} value={r.value}>
                        {t(r.key)}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label={t("auth.department")}>
                  <select
                    value={form.department_id}
                    onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                    className="border border-[#DCD5C0] rounded-md px-3 py-2 text-sm w-full bg-white"
                  >
                    <option value="">{t("auth.notDepartmentSpecific")}</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
                {ROLES.find((r) => r.value === form.role)?.needsInvite && (
                  <Field label={t("auth.inviteCode")}>
                    <input
                      required
                      value={form.invite_code}
                      onChange={(e) => setForm({ ...form, invite_code: e.target.value })}
                      className="border border-[#DCD5C0] rounded-md px-3 py-2 text-sm w-full"
                      placeholder={t("auth.invitePlaceholder")}
                    />
                  </Field>
                )}
              </>
            )}

            {error && (
              <div className="bg-[#F7E6E3] border border-[#E8BEB6] rounded-lg px-3 py-2.5 text-xs text-danger flex items-center gap-2">
                <AlertTriangle size={13} /> {error}
              </div>
            )}

            <button
              disabled={busy}
              type="submit"
              className="bg-navy text-white font-semibold text-sm py-2.5 rounded-md flex items-center justify-center gap-2 mt-1.5 disabled:opacity-60"
            >
              {busy && <Loader2 size={14} className="animate-spin" />}
              {mode === "login" ? t("auth.login") : t("auth.createAccount")}
            </button>
          </form>
        </div>

        <div className="text-[11px] text-[#8A8371] text-center mt-5 flex items-center justify-center gap-1.5">
          <ShieldCheck size={12} /> {t("auth.authorizedOnly")}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11.5px] font-semibold text-[#5A5646] uppercase tracking-wide">{label}</span>
      {children}
    </label>
  );
}
