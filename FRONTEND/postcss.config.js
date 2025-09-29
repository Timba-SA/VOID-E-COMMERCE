// En FRONTEND/postcss.config.js

export default {
  plugins: {
    // ¡EL CAMBIO ESTÁ ACÁ!
    // En lugar de 'tailwindcss', le decimos que use '@tailwindcss/postcss'
    '@tailwindcss/postcss': {},
    'autoprefixer': {},
  },
}