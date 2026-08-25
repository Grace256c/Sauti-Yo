import { Outlet } from "react-router-dom";

import Header from "./Header";
import Footer from "./Footer";

export default function AppShell() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Header />

      <main>
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}