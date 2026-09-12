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
          primary: '#F05252',
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
          green: '#22C55E',
          50: '#FFF5F2',
          100: '#FFEADF',
          200: '#FFC8B3',
          300: '#FF9F7A',
          400: '#FF6B3D',
          500: '#E84E1B', // Color de marca principal Movilnet
          600: '#D23F10', // Hover primario
          700: '#C63D10', // Dark / Active
          800: '#9E2C09',
          900: '#6B1B04',
        }
        
      }
    }
  },
  plugins: [],
}