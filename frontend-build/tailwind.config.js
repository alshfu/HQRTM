/** Tailwind config för production-bygget (se frontend-build/README.md). */
module.exports = {
  darkMode: "class",
  content: [
    "../web/templates/**/*.html",
    "../web/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: { accent: { DEFAULT: "#15b878", ink: "#04140d" } },
      fontFamily: {
        sans: ["Schibsted Grotesk", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
