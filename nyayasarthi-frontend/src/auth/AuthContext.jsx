import React, { createContext, useCallback, useContext, useState } from "react";
import * as api from "../api";

const AuthContext = createContext(null);

/**
 * Holds the logged-in officer's session (JWT + basic profile) in memory and
 * in localStorage, so a page refresh doesn't force a re-login. Every screen
 * in the app reads auth state through useAuth() rather than touching
 * localStorage or api.js directly.
 */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(api.TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(api.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });

  const persistSession = useCallback((accessToken, profile) => {
    localStorage.setItem(api.TOKEN_KEY, accessToken);
    localStorage.setItem(api.USER_KEY, JSON.stringify(profile));
    setToken(accessToken);
    setUser(profile);
  }, []);

  const login = useCallback(
    async (email, password) => {
      const res = await api.login(email, password);
      const profile = { full_name: res.data.full_name, role: res.data.role };
      persistSession(res.data.access_token, profile);
      return profile;
    },
    [persistSession]
  );

  const signup = useCallback(
    async (form) => {
      const res = await api.signup(form);
      const profile = { full_name: res.data.full_name, role: res.data.role };
      persistSession(res.data.access_token, profile);
      return profile;
    },
    [persistSession]
  );

  const loginWithGoogle = useCallback(
    async (credential) => {
      const res = await api.googleAuth(credential);
      const profile = { full_name: res.data.full_name, role: res.data.role };
      persistSession(res.data.access_token, profile);
      return profile;
    },
    [persistSession]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(api.TOKEN_KEY);
    localStorage.removeItem(api.USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, signup, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an <AuthProvider>");
  return ctx;
}
