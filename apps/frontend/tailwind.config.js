/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "midnight": "#0b0f1a",
        "slate-ink": "#111827",
        "ember": "#f97316"
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Instrument Sans'", "sans-serif"],
      }
    },
  },
  plugins: [],
};
