import { useContext } from 'react';
import { LanguageContext } from './LanguageContext';
import { translations } from './translations';

export function useTranslation() {
  const { language } = useContext(LanguageContext);

  const t = (key, params = {}) => {
    // Get translation for current language, fallback to English
    let text = translations[language]?.[key] || translations.en[key] || key;

    // Handle string interpolation for {variable} placeholders
    if (typeof text === 'string' && params) {
      Object.keys(params).forEach(param => {
        text = text.replace(`{${param}}`, params[param]);
      });
    }

    return text;
  };

  const plural = (key, count) => {
    const pluralKey = `plural.${key}`;
    const forms = translations[language]?.[pluralKey] || translations.en[pluralKey];

    if (!forms || !Array.isArray(forms)) {
      return key;
    }

    // Get the correct plural form based on language and count
    let formIndex;
    if (language === 'cs') {
      // Czech: 3 forms
      if (count === 1) formIndex = 0;
      else if (count >= 2 && count <= 4) formIndex = 1;
      else formIndex = 2;
    } else {
      // English: 2 forms
      formIndex = count === 1 ? 0 : 1;
    }

    return forms[formIndex] || forms[0];
  };

  return { t, language, plural };
}
