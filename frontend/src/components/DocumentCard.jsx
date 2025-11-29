import { formatDate, getDaysBetween } from '../utils/dateUtils';
import { getColorClass } from '../utils/colorUtils';

const DocumentCard = ({ document, index, previousDate }) => {
    const daysBetween = previousDate ? getDaysBetween(previousDate, document.date) : null;

    return (
        <>
            {daysBetween !== null && (
                <div className="flex flex-col items-center my-4">
                    <div className="w-px h-8 bg-slate-200"></div>
                    <div className="flex flex-col items-center gap-1 py-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                        <span className="text-xs font-medium text-slate-500">
                            {daysBetween} {daysBetween === 1 ? 'day' : 'days'}
                        </span>
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                    </div>
                    <div className="w-px h-8 bg-slate-200"></div>
                </div>
            )}
            <article className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 mb-4">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        {document.typ && (
                            <p className="text-sm text-slate-500 mt-0.5">
                                {document.typ}
                            </p>
                        )}
                        <h4 className="text-lg font-semibold text-slate-900">
                            Medical document ({index})
                        </h4>
                    </div>
                    <span className="text-sm text-slate-500">
                        {formatDate(document.date)}
                    </span>
                </div>

                <div className="text-sm leading-relaxed text-slate-700 whitespace-pre-line">
                    {document.highlightedText.map((part, index) =>
                        part.type === 'highlight' ? (
                            <span
                                key={`${document.id}-${index}`}
                                className={`px-1.5 py-0.5 rounded-full border ${getColorClass(part.color)} font-medium`}
                            >
                                {part.content}
                            </span>
                        ) : (
                            <span key={`${document.id}-${index}`}>{part.content}</span>
                        ),
                    )}
                </div>
            </article>
        </>
    );
};

export default DocumentCard;

