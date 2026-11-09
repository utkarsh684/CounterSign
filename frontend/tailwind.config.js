/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F7F8FA",
        surface: "#FFFFFF",
        primaryText: "#101828",
        secondaryText: "#667085",
        borderSubtle: "#E4E7EC",
        accent: {
          DEFAULT: "#1D4ED8",
          hover: "#1E40AF",
          light: "#EFF4FF",
        },
        success: {
          DEFAULT: "#067647",
          light: "#ECFDF3",
          border: "#A6F4C5",
        },
        warning: {
          DEFAULT: "#B54708",
          light: "#FFFAEB",
          border: "#FEDF89",
        },
        danger: {
          DEFAULT: "#B42318",
          light: "#FEF3F2",
          border: "#FECDCA",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(16, 24, 40, 0.05), 0 1px 2px 0 rgba(16, 24, 40, 0.03)",
        card: "0 4px 6px -1px rgba(16, 24, 40, 0.05), 0 2px 4px -2px rgba(16, 24, 40, 0.03)",
        elevated: "0 12px 16px -4px rgba(16, 24, 40, 0.08), 0 4px 6px -2px rgba(16, 24, 40, 0.03)",
      },
    },
  },
  plugins: [],
}
