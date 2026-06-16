export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      colors: {
        ink: {
          DEFAULT: "#1a1a2e",
          light: "#2d2d4e",
        },
        parchment: {
          DEFAULT: "#f5f0e8",
          dark: "#e8e0d0",
        },
        gold: {
          DEFAULT: "#c9a84c",
          light: "#e2c97e",
          dark: "#9a7a2e",
        },
        muted: "#6b6b8a",
      },
    },
  },
  plugins: [],
};
