import { useState, useEffect } from 'react';
import { fetchDashboard } from '../services/api';
import Greeting from '../components/Greeting';
import PatientCard from '../components/PatientCard';

const PatientSelection = () => {
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadDashboard = async () => {
            try {
                setLoading(true);
                const data = await fetchDashboard();
                setDashboardData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        loadDashboard();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
                <div className="text-slate-500">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
                <div className="text-red-500">Error: {error}</div>
            </div>
        );
    }

    if (!dashboardData) {
        return (
            <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
                <div className="text-slate-500">No data available</div>
            </div>
        );
    }
    console.log(dashboardData);

    const highlights = [
        { label: 'Patients today', value: dashboardData.totalPatients, caption: 'ready for review' },
        { label: 'Total pages', value: dashboardData.totalPages, caption: 'documents for review' },
        { label: 'Relevant pages', value: dashboardData.relevantPages, caption: 'flagged for findings' },
        { label: 'Unanswered questions', value: dashboardData.patients.reduce((sum, patient) => sum + patient.missingAnswers.length, 0), caption: 'pending clarity' },
    ];

    return (
        <div className="min-h-screen bg-[#f5f5f7] py-10 px-4 text-slate-900">
            <div className="max-w-6xl mx-auto space-y-10">
                <header>
                    <Greeting />
                </header>

                <section className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-8 space-y-8">
                    <div className="flex items-start justify-between flex-wrap gap-4">
                        <div>
                            <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                                Executive summary
                            </p>
                            <h2 className="text-3xl font-semibold text-slate-900 mt-2">
                                Summary of your day
                            </h2>
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

                    <div className="text-base text-slate-700 leading-relaxed border-t border-slate-100 pt-6 space-y-4">
                        {dashboardData.summary && (
                            <p>
                                {dashboardData.summary}
                            </p>
                        )}
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
                    <div className="grid grid-cols-1 gap-6">
                        {dashboardData.patients.map((patient) => (
                            <PatientCard key={patient.id} patient={patient} />
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
};

export default PatientSelection;

