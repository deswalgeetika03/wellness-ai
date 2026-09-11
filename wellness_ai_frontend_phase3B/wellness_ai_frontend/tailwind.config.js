/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        wa: {
          canvasTop: "var(--wa-canvas-top)",
          canvasBottom: "var(--wa-canvas-bottom)",
          sidebar: "var(--wa-sidebar-bg)",
          surface: "var(--wa-surface)",
          border: "var(--wa-border)",
          text: "var(--wa-text)",
          muted: "var(--wa-muted)",
          accent: "var(--wa-accent)",
          accentSoft: "var(--wa-accent-soft)",
        },
      },
      borderRadius: {
        wa: "var(--wa-radius)",
        "wa-sm": "var(--wa-radius-sm)",
      },
    },
  },
  plugins: [],
};