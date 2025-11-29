import { useState } from 'react';
import { formatDate, getDaysBetween } from '../utils/dateUtils';

const DocumentCard = ({ document, index, previousDate, selectedQuestionIds = [], onHoverQuestion }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
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
            <article className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 mb-3 pb-3">
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="w-full flex justify-between items-start mb-4 text-left hover:opacity-80 transition-opacity"
                >
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
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-slate-500">
                            {formatDate(document.date)}
                        </span>
                        <svg
                            className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${isCollapsed ? '' : 'rotate-180'}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                </button>

                <div
                    className={`overflow-hidden transition-all duration-300 ease-in-out ${isCollapsed ? 'max-h-0 opacity-0' : 'max-h-[5000px] opacity-100'
                        }`}
                >
                    <div className="text-sm leading-relaxed text-slate-700 whitespace-pre-line mb-3">
                        {document.highlightedText.map((part, idx) => {
                            if (part.type === 'highlight') {
                                const shouldHighlight = selectedQuestionIds.length === 0 || (part.questionId && selectedQuestionIds.includes(part.questionId));
                                return (
                                    <span
                                        key={`${document.id}-${idx}`}
                                        className={`px-1.5 py-0.5 rounded-full border font-medium ${shouldHighlight
                                            ? ''
                                            : 'bg-slate-100 text-slate-500 border-slate-200'
                                            }`}
                                        style={shouldHighlight ? { backgroundColor: part.color } : undefined}
                                        onMouseEnter={() => onHoverQuestion && onHoverQuestion(part.questionId)}
                                        onMouseLeave={() => onHoverQuestion && onHoverQuestion(null)}
                                    >
                                        {part.content}
                                    </span>
                                );
                            }
                            return <span key={`${document.id}-${idx}`}>{part.content}</span>;
                        })}
                    </div>
                </div>
            </article >
        </>
    );
};

export default DocumentCard;

