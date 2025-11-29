const DifficultyRating = ({ rating }) => {
    return (
        <div className="text-right" aria-label={`Difficulty ${rating} out of 5`}>
            <div className="flex items-center gap-1 justify-end mb-1">
                {[1, 2, 3, 4, 5].map((level) => (
                    <span
                        key={level}
                        className={`h-1.5 w-6 rounded-full transition-colors ${level <= rating ? 'bg-slate-900' : 'bg-slate-200'
                            }`}
                    />
                ))}
            </div>
            <span className="text-xs font-medium text-slate-500">Difficulty {rating}/5</span>
        </div>
    );
};

export default DifficultyRating;

