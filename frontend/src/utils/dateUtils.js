export const formatDate = (dateString, language = 'cs') => {
    const date = new Date(dateString);
    const locale = language === 'cs' ? 'cs-CZ' : 'en-US';
    return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: language === 'cs' ? 'numeric' : 'short',
        day: 'numeric'
    });
};

export const formatDateRange = (startDate, endDate, language = 'cs') => {
    const start = formatDate(startDate, language);
    const end = formatDate(endDate, language);
    return `${start} - ${end}`;
};

export const getYearsSpan = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const years = Math.round((end - start) / (365.25 * 24 * 60 * 60 * 1000));
    return years;
};

export const getDaysBetween = (date1, date2) => {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diffTime = Math.abs(d2 - d1);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
};

