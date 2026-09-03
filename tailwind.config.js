/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        movilnet: {
          primary: '#C93B3B',
          'primary-hover': '#B22E2E',
          accent: '#F05252',
          'accent-hover': '#E03E3E',
          bg: '#F4F4F4',
          card: '#FFFFFF',
          input: '#FAFAFA',
          'input-border': '#E5E5E5',
          dark: '#1F1F1F',
          muted: '#737373',
          'muted-light': '#9CA3AF',
          green: '#22C55E'
        }
      }
    }
  },
  plugins: [],
}