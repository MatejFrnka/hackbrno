import { getColorBgClass } from '../utils/colorUtils';
import { formatDate } from '../utils/dateUtils';

const Timeline = ({ documents, questions, onDocumentClick, currentDate }) => {
    if (documents.length === 0) return null;

    // Get all unique dates and sort them
    const sortedDates = [...new Set(documents.map(doc => doc.date))].sort((a, b) => new Date(a) - new Date(b));
    const startDate = sortedDates[0];
    const endDate = sortedDates[sortedDates.length - 1];

    const startTime = new Date(startDate).getTime();
    const endTime = new Date(endDate).getTime();
    const totalTime = endTime - startTime;

    // Calculate position of current date
    const currentPosition = currentDate && totalTime > 0
        ? ((new Date(currentDate).getTime() - startTime) / totalTime) * 100
        : null;

    // Group documents by date with their colors and document IDs
    const documentsByDate = {};
    documents.forEach((doc) => {
        if (!documentsByDate[doc.date]) {
            documentsByDate[doc.date] = { colors: {}, docIds: {} };
        }
        doc.highlights.forEach((h) => {
            if (!documentsByDate[doc.date].colors[h.color]) {
                documentsByDate[doc.date].colors[h.color] = true;
                documentsByDate[doc.date].docIds[h.color] = doc.id;
            }
        });
    });

    // Calculate positions for each date
    const timelinePoints = sortedDates.map((date) => {
        const dateTime = new Date(date).getTime();
        const position = totalTime > 0 ? ((dateTime - startTime) / totalTime) * 100 : 0;
        const dateData = documentsByDate[date] || { colors: {}, docIds: {} };
        const colors = Object.keys(dateData.colors);
        const docIds = dateData.docIds;
        return { date, position, colors, docIds };
    });

    return (
        <aside className="hidden lg:flex w-24 sticky top-24 h-[calc(100vh-8rem)]">
            <div className="relative flex-1 flex flex-col pt-8">
                {/* Start date at top */}
                <div className="text-center mb-2">
                    <p className="text-[10px] text-slate-500 font-medium">
                        {formatDate(startDate)}
                    </p>
                </div>

                {/* Timeline line and dots */}
                <div className="relative flex-1 flex justify-center">
                    <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-px bg-slate-200" />

                    {/* Black line indicating current position */}
                    {currentPosition !== null && (
                        <div
                            className="absolute left-1/2 -translate-x-1/2 z-30 flex items-center transition-all duration-300 ease-in-out"
                            style={{
                                top: `${currentPosition}%`,
                                transform: 'translateX(-50%) translateY(-50%)'
                            }}
                        >
                            <div className="w-8 h-0.5 bg-slate-500"></div>
                        </div>
                    )}

                    {timelinePoints.map((point) => (
                        <div
                            key={point.date}
                            className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5"
                            style={{ top: `${point.position}%` }}
                        >
                            {point.colors.map((color) => {
                                const question = questions.find((q) => q.color === color);
                                const docId = point.docIds[color];
                                return (
                                    <div key={`${point.date}-${color}`} className="relative group">
                                        <button
                                            type="button"
                                            onClick={() => onDocumentClick && onDocumentClick(docId)}
                                            className={`w-3 h-3 rounded-full ${getColorBgClass(
                                                color,
                                            )} border-2 border-white shadow-sm hover:scale-125 transition-transform relative z-10 cursor-pointer`}
                                            title={question ? question.text : color}
                                        />
                                        {/* Hover tooltip for date */}
                                        <span className="absolute left-full ml-2 top-1/2 -translate-y-1/2 text-xs text-slate-600 bg-white border border-slate-200 rounded px-2 py-1 shadow-sm opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity z-20">
                                            {formatDate(point.date)}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    ))}
                </div>

                {/* End date at bottom */}
                <div className="text-center mt-2">
                    <p className="text-[10px] text-slate-500 font-medium">
                        {formatDate(endDate)}
                    </p>
                </div>
            </div>
        </aside>
    );
};

export default Timeline;

