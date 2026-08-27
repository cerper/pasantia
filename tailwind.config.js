/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        movilnet: {
          // Rojo principal corporativo (panel izquierdo y botones)
          primary: '#C93B3B',
          'primary-hover': '#B22E2E',
          
          // Rojo secundario / coral (botón Iniciar sesión)
          accent: '#F05252',
          'accent-hover': '#E03E3E',
          
          // Fondos claros e inputs
          bg: '#F4F4F4',          // Fondo general de la pantalla
          card: '#FFFFFF',        // Fondo del contenedor blanco
          input: '#FAFAFA',       // Fondo claro de los inputs
          'input-border': '#E5E5E5', // Borde suave de los inputs
          
          // Tipografía
          dark: '#1F1F1F',        // Títulos y texto principal ("Bienvenido de nuevo")
          muted: '#737373',       // Subtítulos y etiquetas secundarias
          'muted-light': '#9CA3AF', // Placeholders y textos muy suaves
          
          // Acentos adicionales
          green: '#22C55E'        // Indicador de estado activo (punto verde)
        }
      }
    }
  },
  plugins: [],
}