export const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
};

export const formatDateRange = (startDate, endDate) => {
    const start = formatDate(startDate);
    const end = formatDate(endDate);
    return `${start} - ${end}`;
};

export const getYearsSpan = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const years = Math.round((end - start) / (365.25 * 24 * 60 * 60 * 1000));
    return years;
};

