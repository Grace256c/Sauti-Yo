import { useEffect } from "react";
import { X } from "lucide-react";

// A neutral, unrelated page to jump to instantly. Deliberately not
// Sauti Yo or anything that could look like it was left open on purpose.
const SAFE_EXIT_URL = "https://www.google.com";

function exitNow() {
  // location.replace (not .href) swaps the current history entry instead
  // of adding one, so the browser's Back button skips over this site
  // entirely and lands on whatever page was open before it.
  window.location.replace(SAFE_EXIT_URL);
}

export default function QuickExit() {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        exitNow();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <button
      type="button"
      onClick={exitNow}
      aria-label="Quick exit this site and go to a neutral page"
      title="Quickly leave this site (or press Esc)"
      className="
        fixed right-3 top-3 z-[100]
        flex items-center gap-1.5
        rounded-full bg-red-600 px-3.5 py-2
        text-xs font-bold uppercase tracking-wide text-white
        shadow-lg transition
        hover:bg-red-700
        focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2
        sm:right-4 sm:top-4 sm:text-sm
      "
    >
      <X className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
      Quick Exit
    </button>
  );
}
