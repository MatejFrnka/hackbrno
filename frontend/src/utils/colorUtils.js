// Color utilities for question highlighting
export const getColorClass = (color) => {
    const colorMap = {
        blue: 'bg-blue-50 text-blue-900 border-blue-200',
        red: 'bg-red-50 text-red-900 border-red-200',
        green: 'bg-green-50 text-green-900 border-green-200',
        yellow: 'bg-yellow-50 text-yellow-900 border-yellow-200',
        purple: 'bg-purple-50 text-purple-900 border-purple-200',
        orange: 'bg-orange-50 text-orange-900 border-orange-200',
        pink: 'bg-pink-50 text-pink-900 border-pink-200',
        cyan: 'bg-cyan-50 text-cyan-900 border-cyan-200',
    };
    return colorMap[color] || 'bg-slate-50 text-slate-900 border-slate-200';
};

export const getColorBgClass = (color) => {
    const colorMap = {
        blue: 'bg-blue-500',
        red: 'bg-red-500',
        green: 'bg-green-500',
        yellow: 'bg-yellow-500',
        purple: 'bg-purple-500',
        orange: 'bg-orange-500',
        pink: 'bg-pink-500',
        cyan: 'bg-cyan-500',
    };
    return colorMap[color] || 'bg-slate-400';
};

export const getColorBorderClass = (color) => {
    const colorMap = {
        blue: 'border-blue-500',
        red: 'border-red-500',
        green: 'border-green-500',
        yellow: 'border-yellow-500',
        purple: 'border-purple-500',
        orange: 'border-orange-500',
        pink: 'border-pink-500',
        cyan: 'border-cyan-500',
    };
    return colorMap[color] || 'border-slate-400';
};

