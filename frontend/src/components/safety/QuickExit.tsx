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
        flex h-11 items-center gap-1.5
        rounded-md border border-red-600/50 bg-surface/95
        px-3.5 text-xs font-semibold text-red-600
        shadow-sm backdrop-blur-md transition-all duration-200
        hover:border-red-600 hover:bg-red-600 hover:text-white
        focus:outline-none focus:ring-2 focus:ring-red-500/30
        dark:text-red-500 dark:hover:text-white
        sm:right-4 sm:top-4 sm:text-sm
      "
    >
      <X className="h-4 w-4" />
      Quick Exit
    </button>
  );
}
