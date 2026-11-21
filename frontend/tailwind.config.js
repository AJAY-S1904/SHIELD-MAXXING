/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        aero: {
          cyan: '#0df2c9',
          blue: '#00a3ff',
          deep: '#032541',
          teal: '#0a647d',
          glass: 'rgba(255, 255, 255, 0.15)',
        }
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'aero-window': '0 25px 60px -15px rgba(0, 30, 60, 0.6), 0 0 40px rgba(0, 163, 255, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.8)',
        'aero-panel': 'inset 0 1px 1px rgba(255, 255, 255, 0.6), 0 8px 32px 0 rgba(0, 50, 80, 0.35)',
        'aero-button': 'inset 0 1px 0 rgba(255, 255, 255, 0.7), 0 4px 15px rgba(0, 163, 255, 0.35)',
        'aero-glow-safe': '0 0 35px rgba(16, 185, 129, 0.5), inset 0 0 20px rgba(16, 185, 129, 0.3)',
        'aero-glow-danger': '0 0 35px rgba(239, 68, 68, 0.6), inset 0 0 20px rgba(239, 68, 68, 0.3)',
      }
    },
  },
  plugins: [],
};
