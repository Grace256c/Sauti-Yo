import { Outlet } from "react-router-dom";

import Header from "./Header";
import Footer from "./Footer";
import ChatWidget from "../chat/chatwidget";
import QuickExit from "../safety/QuickExit";

export default function AppShell() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <QuickExit />

      <Header />

      <main>
        <Outlet />
      </main>

      <Footer />

      <ChatWidget />
    </div>
  );
}