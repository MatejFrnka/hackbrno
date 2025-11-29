
const ColorFilter = ({
    items = [],
    selectedIds = [],
    onToggle,
    onClear,
    compact = false,
    label = 'Filter',
    showColorIndicator = false,
    hoveredId = null
}) => {
    if (compact) {
        return (
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <p className="text-[10px] uppercase tracking-wide text-slate-500 font-medium">
                        {label}
                    </p>
                    {selectedIds?.length > 0 && onClear && (
                        <button
                            onClick={onClear}
                            className="text-[10px] text-slate-400 hover:text-slate-600 transition-colors"
                        >
                            Clear
                        </button>
                    )}
                </div>
                <div className="flex flex-col gap-1.5">
                    {items?.map((item) => {
                        const isSelected = selectedIds?.includes(item.id);
                        const isHovered = hoveredId !== null && Number(item.id) === Number(hoveredId);
                        return (
                            <button
                                key={item.id}
                                type="button"
                                onClick={() => onToggle(item.id)}
                                className={`group flex items-start gap-2 rounded-lg px-2 py-1.5 text-left transition-all ${isSelected
                                    ? 'bg-slate-900'
                                    : 'hover:bg-slate-50'
                                    }`}
                            >
                                {showColorIndicator ? (
                                    <span
                                        className={`w-3 h-3 rounded-full flex-shrink-0 mt-0.5 ${isSelected ? 'ring-2 ring-white' : ''
                                            }`}
                                        aria-hidden="true"
                                        style={{ backgroundColor: item.color }}
                                    />
                                ) : (
                                    <span
                                        className={`w-3 h-3 rounded flex-shrink-0 mt-0.5 ${isSelected ? 'bg-white' : 'bg-slate-300'
                                            }`}
                                        aria-hidden="true"
                                    />
                                )}
                                <span className={`text-[11px] leading-tight transition-[font-weight] duration-200 ${isSelected ? 'text-white' : 'text-slate-600'
                                    } ${isHovered ? 'font-bold' : ''}`}>
                                    {item.label || item.text}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
                <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                        Filters
                    </p>
                    <h3 className="text-lg font-semibold text-slate-900">
                        {label}
                    </h3>
                </div>
                {selectedIds.length > 0 && onClear && (
                    <button
                        onClick={onClear}
                        className="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors"
                    >
                        Clear all
                    </button>
                )}
            </div>

            <div className="flex flex-wrap gap-2">
                {items.map((item) => {
                    const isSelected = selectedIds.includes(item.id);
                    const isHovered = hoveredId !== null && item.id === hoveredId;
                    return (
                        <button
                            key={item.id}
                            type="button"
                            onClick={() => onToggle(item.id)}
                            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm border transition-colors ${isSelected
                                ? 'border-slate-900 bg-slate-900 text-white'
                                : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300'
                                }`}
                        >
                            {showColorIndicator && item.color && (
                                <span
                                    className={`w-2.5 h-2.5 rounded-full`}
                                    style={{ backgroundColor: item.color }}
                                    aria-hidden="true"
                                />
                            )}
                            <span className={`text-left transition-[font-weight] duration-200 ${isHovered ? 'font-bold' : ''}`}>{item.label || item.text}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default ColorFilter;

