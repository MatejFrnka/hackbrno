import { useNavigate } from 'react-router-dom';
import { formatDateRange } from '../utils/dateUtils';
import DifficultyRating from './DifficultyRating';

const PatientCard = ({ patient }) => {
    const navigate = useNavigate();
    const handleReview = (e) => {
        e.stopPropagation();
        navigate(`/patient/${encodeURIComponent(patient.id)}`);
    };

    const ColorChip = ({ item, label }) => {
        return (
            <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 bg-white/80">
                <span
                    className={`w-2.5 h-2.5 rounded-full`}
                    style={{ backgroundColor: item.rgb_color }}
                    aria-hidden="true"
                />
                <span className="text-slate-900 font-medium">{item.name}</span>
                <span className="text-slate-500">
                    {item.documents_count} {label}
                </span>
            </span>
        )
    };

    return (
        <article className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-6 flex flex-col gap-5">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400 mb-2">
                        Patient
                    </p>
                    <h3 className="text-2xl font-semibold text-slate-900">
                        {patient.name}
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
                        {patient.relevantDocuments} relevant
                        <span className="text-sm text-slate-500">, {patient.totalDocuments} total</span>
                    </p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                        Answers
                    </p>
                    <p className="text-lg font-semibold text-slate-900 mt-2">
                        {patient.locatedAnswers.length}
                        <span className="text-sm text-slate-500"> out of {patient.locatedAnswers.length + patient.missingAnswers.length} found</span>
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                        Located answers
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {patient.locatedAnswers.length > 0 ? (
                            patient.locatedAnswers.map((item) => (
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
                        {patient.missingAnswers.length > 0 ? (
                            patient.missingAnswers.map((item) => (
                                <ColorChip
                                    key={`${patient.id}-${item.id}-missing`}
                                    item={item}
                                    value={item.unanswered}
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

            <div className="pt-2 flex justify-end">
                <button
                    onClick={handleReview}
                    className="inline-flex items-center gap-2 bg-slate-900 text-white rounded-xl px-5 py-2.5 text-sm font-semibold hover:bg-slate-800 hover:shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-slate-900/20"
                >
                    Review
                    <span>→</span>
                </button>
            </div>
        </article>
    );
};

export default PatientCard;

