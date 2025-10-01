import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpApi from 'i18next-http-backend';

i18n
  .use(HttpApi) // Carga traducciones desde una URL
  .use(LanguageDetector) // Detecta el idioma del usuario
  .use(initReactI18next) // Integra i18next con React
  .init({
    supportedLngs: ['en', 'es'],
    fallbackLng: 'en',
    detection: {
      order: ['cookie', 'localStorage', 'htmlTag', 'path', 'subdomain'],
      caches: ['cookie'], // Dónde guarda la elección del usuario
    },
    backend: {
      loadPath: '/locales/{{lng}}/translation.json', // Dónde buscar los JSON
    },
    react: { useSuspense: false },
  });

export default i18n;