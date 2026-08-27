import {
  StrictMode,
} from "react";
import {
  createRoot,
} from "react-dom/client";
import {
  RouterProvider,
} from "react-router-dom";

import "./index.css";
import "./i18n";

import {
  PartnerAuthProvider,
} from "./context/PartnerAuthContext";

import {
  router,
} from "./router";

createRoot(
  document.getElementById("root")!,
).render(
  <StrictMode>
    <PartnerAuthProvider>
      <RouterProvider
        router={router}
      />
    </PartnerAuthProvider>
  </StrictMode>,
);
