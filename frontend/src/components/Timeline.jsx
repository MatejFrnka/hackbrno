import { getColorBgClass } from '../utils/colorUtils';
import { formatDate } from '../utils/dateUtils';

const Timeline = ({ documents, questions, onColorClick }) => {
    const timelineData = [];
    documents.forEach((doc) => {
        const colors = [...new Set(doc.highlights.map((h) => h.color))];
        if (colors.length > 0) {
            timelineData.push({
                date: doc.date,
                colors,
            });
        }
    });

    const groupedByDate = {};
    timelineData.forEach((item) => {
        if (!groupedByDate[item.date]) {
            groupedByDate[item.date] = [];
        }
        item.colors.forEach((color) => {
            if (!groupedByDate[item.date].includes(color)) {
                groupedByDate[item.date].push(color);
            }
        });
    });

    const sortedDates = Object.keys(groupedByDate).sort((a, b) => new Date(a) - new Date(b));

    return (
        <aside className="hidden lg:flex w-24 sticky top-24 h-[calc(100vh-8rem)]">
            <div className="relative flex-1">
                <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-px bg-slate-200 rounded-full" />
                <div className="flex flex-col items-center gap-6 pt-4">
                    <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400">
                        Timeline
                    </p>
                    {sortedDates.map((date) => (
                        <div key={date} className="flex flex-col items-center gap-2">
                            <div className="flex flex-col items-center gap-1.5">
                                {groupedByDate[date].map((color) => {
                                    const question = questions.find((q) => q.color === color);
                                    return (
                                        <button
                                            key={`${date}-${color}`}
                                            type="button"
                                            onClick={() => onColorClick && onColorClick(color)}
                                            className={`w-4 h-4 rounded-full ${getColorBgClass(
                                                color,
                                            )} border-2 border-white shadow-sm hover:scale-125 transition-transform`}
                                            title={question ? question.text : color}
                                        />
                                    );
                                })}
                            </div>
                            <span className="text-[10px] text-slate-500 -rotate-90 origin-center inline-block">
                                {formatDate(date)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </aside>
    );
};

export default Timeline;

