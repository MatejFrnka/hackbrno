import { patients, getExecutiveSummary } from '../data/mockData';
import Greeting from '../components/Greeting';
import PatientCard from '../components/PatientCard';

const PatientSelection = () => {
    const summary = getExecutiveSummary();
    const { large, medium, small } = summary.dataAmountBreakdown;

    const highlights = [
        { label: 'Patients today', value: summary.totalPatients, caption: 'ready for review' },
        { label: 'Total pages', value: summary.totalPages, caption: 'all documents collected' },
        { label: 'Relevant pages', value: summary.relevantPages, caption: 'flagged for findings' },
        { label: 'Unanswered questions', value: summary.totalMissing, caption: 'pending clarity' },
    ];

    return (
        <div className="min-h-screen bg-[#f5f5f7] py-10 px-4 text-slate-900">
            <div className="max-w-6xl mx-auto space-y-10">
                <header>
                    <Greeting />
                    <p className="text-base text-slate-500">
                        Your day is curated below—ten patients, their timelines, and the answers we traced.
                    </p>
                </header>

                <section className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-8 space-y-8">
                    <div className="flex items-start justify-between flex-wrap gap-4">
                        <div>
                            <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                                Executive summary
                            </p>
                            <h2 className="text-3xl font-semibold text-slate-900 mt-2">
                                Summary of the work to be done
                            </h2>
                        </div>
                        <div className="text-sm text-slate-500">
                            <p>{large} patients with a large volume of data</p>
                            <p>{medium} with a medium amount</p>
                            <p>{small} with a concise record</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {highlights.map((item) => (
                            <div
                                key={item.label}
                                className="rounded-2xl border border-slate-100 bg-slate-50/60 p-5"
                            >
                                <p className="text-xs uppercase tracking-wide text-slate-500">
                                    {item.label}
                                </p>
                                <p className="text-3xl font-semibold text-slate-900 mt-2">
                                    {item.value}
                                </p>
                                <p className="text-sm text-slate-500">{item.caption}</p>
                            </div>
                        ))}
                    </div>

                    <div className="text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-6 space-y-2">
                        <p>
                            You have {summary.totalPatients} patients to review today. Total pages to review is{' '}
                            {summary.totalPages}, out of which {summary.relevantPages} contain relevant information.
                        </p>
                        <p>We did not find answers to {summary.totalMissing} questions.</p>
                    </div>
                </section>

                <section className="space-y-6">
                    <div>
                        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                            Patient overview
                        </p>
                        <h2 className="text-2xl font-semibold text-slate-900 mt-2">
                            List of patients
                        </h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {patients.map((patient) => (
                            <PatientCard key={patient.id} patient={patient} />
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
};

export default PatientSelection;

