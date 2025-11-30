import React, { createContext, useState, useEffect } from 'react';

export const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    // Load language preference from localStorage, default to Czech
    const saved = localStorage.getItem('language');
    return saved || 'cs';
  });

  useEffect(() => {
    // Save language preference to localStorage
    localStorage.setItem('language', language);

    // Update HTML lang attribute for accessibility
    document.documentElement.lang = language;
  }, [language]);

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'cs' ? 'en' : 'cs');
  };

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}
