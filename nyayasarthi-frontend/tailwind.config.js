/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F6F3EC",
        ink: "#1E2430",
        navy: "#1B3A5C",
        gold: "#A67C27",
        okgreen: "#2F7D5B",
        warnamber: "#C68A1F",
        danger: "#B54A3F",
      },
      fontFamily: {
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
