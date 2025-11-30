import { translations } from './translations';

/**
 * Get Czech plural form index
 * Czech has 3 plural forms:
 * - 0: singular (1)
 * - 1: paucal (2-4)
 * - 2: plural (0, 5+)
 */
export function getCzechPluralForm(count) {
  if (count === 1) return 0;
  if (count >= 2 && count <= 4) return 1;
  return 2;
}

/**
 * Get English plural form index
 * English has 2 plural forms:
 * - 0: singular (1)
 * - 1: plural (0, 2+)
 */
export function getEnglishPluralForm(count) {
  return count === 1 ? 0 : 1;
}

/**
 * Get the correct plural form for a given key and count
 */
export function getPlural(key, count, language) {
  const pluralKey = `plural.${key}`;
  const forms = translations[language]?.[pluralKey] || translations.en[pluralKey];

  if (!forms || !Array.isArray(forms)) {
    return key;
  }

  let formIndex;
  if (language === 'cs') {
    formIndex = getCzechPluralForm(count);
  } else {
    formIndex = getEnglishPluralForm(count);
  }

  return forms[formIndex] || forms[0];
}

/**
 * Format date according to locale
 * Czech: "30. 11. 2025"
 * English: "Nov 30, 2025"
 */
export function formatDate(dateString, language = 'cs') {
  if (!dateString) return '';

  const date = new Date(dateString);
  const locale = language === 'cs' ? 'cs-CZ' : 'en-US';

  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: language === 'cs' ? 'numeric' : 'short',
    day: 'numeric',
  });
}

/**
 * Format date range
 */
export function formatDateRange(startDate, endDate, language = 'cs') {
  if (!startDate || !endDate) return '';

  const start = formatDate(startDate, language);
  const end = formatDate(endDate, language);

  return `${start} - ${end}`;
}

/**
 * Get "X days" text with correct plural form
 */
export function getDaysBetweenText(count, language = 'cs') {
  const dayWord = getPlural('day', count, language);
  return `${count} ${dayWord}`;
}
