import { formatDate } from '../utils/dateUtils';
import { getColorClass } from '../utils/colorUtils';

const DocumentCard = ({ document }) => {
    return (
        <article className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 mb-4">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                        Medical document
                    </p>
                    <h4 className="text-lg font-semibold text-slate-900 mt-1">
                        Extracted note
                    </h4>
                </div>
                <span className="text-sm text-slate-500">
                    {formatDate(document.date)}
                </span>
            </div>

            <div className="text-sm leading-relaxed text-slate-700">
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
    );
};

export default DocumentCard;

