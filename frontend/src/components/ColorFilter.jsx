import { getColorBgClass } from '../utils/colorUtils';

const ColorFilter = ({ questions, selectedColors, onToggleColor, onClear }) => {
    return (
        <div className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
                <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                        Filters
                    </p>
                    <h3 className="text-lg font-semibold text-slate-900">
                        Filter by question color
                    </h3>
                </div>
                {selectedColors.length > 0 && onClear && (
                    <button
                        onClick={onClear}
                        className="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors"
                    >
                        Clear all
                    </button>
                )}
            </div>

            <div className="flex flex-wrap gap-2">
                {questions.map((question) => {
                    const isSelected = selectedColors.includes(question.color);
                    return (
                        <button
                            key={question.id}
                            type="button"
                            onClick={() => onToggleColor(question.color)}
                            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm border transition-colors ${isSelected
                                    ? 'border-slate-900 bg-slate-900 text-white'
                                    : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300'
                                }`}
                        >
                            <span
                                className={`w-2.5 h-2.5 rounded-full ${getColorBgClass(question.color)}`}
                                aria-hidden="true"
                            />
                            <span className="text-left">{question.text}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default ColorFilter;

