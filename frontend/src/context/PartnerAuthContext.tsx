import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getPartnerSession,
  loginPartner,
  logoutPartner,
} from "../services/partners";

import type {
  PartnerLoginPayload,
  PartnerSession,
} from "../services/partners";

type PartnerAuthContextValue = {
  session: PartnerSession | null;
  loading: boolean;
  authenticated: boolean;
  login: (
    payload: PartnerLoginPayload,
  ) => Promise<PartnerSession>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
};

const PartnerAuthContext =
  createContext<PartnerAuthContextValue | null>(
    null,
  );

export function PartnerAuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [session, setSession] =
    useState<PartnerSession | null>(
      null,
    );

  const [loading, setLoading] =
    useState(true);

  const refreshSession =
    useCallback(async () => {
      try {
        const current =
          await getPartnerSession();

        setSession(current);
      } catch {
        setSession(null);
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  const login = useCallback(
    async (
      payload: PartnerLoginPayload,
    ) => {
      const nextSession =
        await loginPartner(payload);

      setSession(nextSession);

      return nextSession;
    },
    [],
  );

  const logout = useCallback(
    async () => {
      await logoutPartner();

      setSession(null);
    },
    [],
  );

  const value = useMemo(
    () => ({
      session,
      loading,
      authenticated:
        session !== null,
      login,
      logout,
      refreshSession,
    }),
    [
      session,
      loading,
      login,
      logout,
      refreshSession,
    ],
  );

  return (
    <PartnerAuthContext.Provider
      value={value}
    >
      {children}
    </PartnerAuthContext.Provider>
  );
}

export function usePartnerAuth() {
  const context = useContext(
    PartnerAuthContext,
  );

  if (!context) {
    throw new Error(
      "usePartnerAuth must be used inside PartnerAuthProvider.",
    );
  }

  return context;
}
