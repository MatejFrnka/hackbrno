import { useNavigate } from 'react-router-dom';
import { formatDateRange } from '../utils/dateUtils';
import { getColorBgClass } from '../utils/colorUtils';
import DifficultyRating from './DifficultyRating';

const PatientCard = ({ patient }) => {
    const navigate = useNavigate();
    const questionMeta = patient.questions.map((question) => {
        const located = patient.locatedAnswers[question.color] || 0;
        const missing = Math.max(patient.missingAnswers[question.color] || 0, 0);

        return {
            ...question,
            located,
            missing,
        };
    });

    const locatedQuestions = questionMeta.filter((item) => item.located > 0);
    const missingQuestions = questionMeta.filter((item) => item.missing > 0);

    const handleClick = () => {
        navigate(`/patient/${encodeURIComponent(patient.id)}`);
    };

    const handleKeyDown = (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            handleClick();
        }
    };

    const ColorChip = ({ item, value, label }) => (
        <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 bg-white/80">
            <span
                className={`w-2.5 h-2.5 rounded-full ${getColorBgClass(item.color)}`}
                aria-hidden="true"
            />
            <span className="text-slate-900 font-medium">{item.text}</span>
            <span className="text-slate-500">
                {value} {label}
            </span>
        </span>
    );

    return (
        <article
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            role="button"
            tabIndex={0}
            className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 cursor-pointer hover:shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-slate-900/10 flex flex-col gap-5"
        >
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 mb-2">
                        Patient
                    </p>
                    <h3 className="text-2xl font-semibold text-slate-900">
                        {patient.id}
                    </h3>
                    <p className="text-sm text-slate-500 mt-1">
                        {formatDateRange(patient.startDate, patient.endDate)}
                    </p>
                </div>
                <DifficultyRating rating={patient.difficulty} />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                        Documents
                    </p>
                    <p className="text-lg font-semibold text-slate-900 mt-2">
                        {patient.totalDocuments}
                        <span className="text-sm text-slate-500"> / {patient.relevantDocuments} relevant</span>
                    </p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                        Answers
                    </p>
                    <p className="text-lg font-semibold text-slate-900 mt-2">
                        {patient.totalLocated}
                        <span className="text-sm text-slate-500"> located</span>
                    </p>
                    <p className="text-sm text-slate-500">
                        {patient.totalMissing} still missing
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                        Located answers
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {locatedQuestions.length > 0 ? (
                            locatedQuestions.map((item) => (
                                <ColorChip
                                    key={`${patient.id}-${item.id}-located`}
                                    item={item}
                                    value={item.located}
                                    label="docs"
                                />
                            ))
                        ) : (
                            <span className="text-xs text-slate-400">No answers located yet</span>
                        )}
                    </div>
                </div>

                <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                        Missing answers
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {missingQuestions.length > 0 ? (
                            missingQuestions.map((item) => (
                                <ColorChip
                                    key={`${patient.id}-${item.id}-missing`}
                                    item={item}
                                    value={item.missing}
                                    label="pending"
                                />
                            ))
                        ) : (
                            <span className="text-xs text-slate-400">All questions covered</span>
                        )}
                    </div>
                </div>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed">
                {patient.summary}
            </p>
        </article>
    );
};

export default PatientCard;

