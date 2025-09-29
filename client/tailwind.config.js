/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    // ACÁ ESTÁ LA MAGIA, con esta línea agarra todos los archivos
    // de la carpeta 'src' y no tenés que agregar más nada nunca.
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'void-pink': '#FF69B4',
        'void-purple': '#8A2BE2',
        'void-blue': '#00BFFF',
      },
    },
  },
  plugins: [],
}