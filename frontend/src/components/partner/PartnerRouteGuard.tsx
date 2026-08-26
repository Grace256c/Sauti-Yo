import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  usePartnerAuth,
} from "../../context/PartnerAuthContext";

export default function PartnerRouteGuard() {
  const {
    authenticated,
    loading,
  } = usePartnerAuth();

  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-sm text-text-secondary">
          Loading partner workspace...
        </p>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <Navigate
        to="/partner/login"
        replace
        state={{
          from:
            location.pathname,
        }}
      />
    );
  }

  return <Outlet />;
}
