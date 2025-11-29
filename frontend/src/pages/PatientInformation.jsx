import { useState, useMemo, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchPatient } from '../services/api';
import { formatDateRange } from '../utils/dateUtils';
import DocumentCard from '../components/DocumentCard';
import Timeline from '../components/Timeline';
import ColorFilter from '../components/ColorFilter';

const PatientInformation = () => {
    const { id: encodedId } = useParams();
    const navigate = useNavigate();
    const [patient, setPatient] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedColors, setSelectedColors] = useState([]);
    const [selectedTypes, setSelectedTypes] = useState([]);
    const [currentDocumentDate, setCurrentDocumentDate] = useState(null);
    const documentRefs = useRef({});

    const decodedId = encodedId ? decodeURIComponent(encodedId) : '';

    useEffect(() => {
        const loadPatient = async () => {
            try {
                setLoading(true);
                const data = await fetchPatient(decodedId);
                if (data) {
                    // Calculate start and end dates from documents if not provided
                    if (data.documents && data.documents.length > 0) {
                        const dates = data.documents.map(d => d.date).filter(Boolean).sort();
                        if (dates.length > 0) {
                            data.startDate = dates[0];
                            data.endDate = dates[dates.length - 1];
                        }
                    }
                    setPatient(data);
                } else {
                    setError('Patient not found');
                }
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        if (decodedId) {
            loadPatient();
        }
    }, [decodedId]);

    // Get all unique document types
    const documentTypes = useMemo(() => {
        if (!patient) return [];
        const types = [...new Set(patient.documents.map(doc => doc.typ).filter(Boolean))];
        return types.sort();
    }, [patient]);

    // Filter documents by type only (color filter just highlights, doesn't hide)
    const filteredDocuments = useMemo(() => {
        if (!patient) return [];
        if (selectedTypes.length === 0) {
            return patient.documents;
        }
        return patient.documents.filter((doc) => selectedTypes.includes(doc.typ));
    }, [patient, selectedTypes]);

    const handleToggleColor = (color) => {
        setSelectedColors((prev) =>
            prev.includes(color) ? prev.filter((c) => c !== color) : [...prev, color],
        );
    };

    const handleToggleType = (type) => {
        setSelectedTypes((prev) =>
            prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
        );
    };

    const handleDocumentClick = (docId) => {
        const ref = documentRefs.current[docId];
        if (ref) {
            ref.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    };

    // Track which document is currently in view
    useEffect(() => {
        if (filteredDocuments.length === 0) return;

        const observerOptions = {
            root: null,
            rootMargin: '-20% 0px -60% 0px',
            threshold: 0,
        };

        const observerCallback = (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const docId = entry.target.getAttribute('data-doc-id');
                    const document = filteredDocuments.find(d => d.id === docId);
                    if (document) {
                        setCurrentDocumentDate(document.date);
                    }
                }
            });
        };

        const observer = new IntersectionObserver(observerCallback, observerOptions);

        // Observe all document elements
        Object.values(documentRefs.current).forEach((ref) => {
            if (ref) observer.observe(ref);
        });

        return () => {
            Object.values(documentRefs.current).forEach((ref) => {
                if (ref) observer.unobserve(ref);
            });
        };
    }, [filteredDocuments]);

    if (loading) {
        return (
            <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
                <div className="text-slate-500">Loading...</div>
            </div>
        );
    }

    if (error || !patient) {
        return (
            <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center px-4">
                <div className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-8 text-center space-y-4">
                    <h1 className="text-2xl font-semibold text-slate-900">Patient not found</h1>
                    <p className="text-slate-500">{error || 'The identifier you followed does not exist.'}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="text-sm font-medium text-slate-900 underline underline-offset-4"
                    >
                        Return to patient list
                    </button>
                </div>
            </div>
        );
    }

    const summaryStats = [
        { label: 'Total documents', value: patient.totalDocuments, caption: 'complete record' },
        { label: 'Relevant documents', value: patient.relevantDocuments, caption: 'marked for review' },
        { label: 'Located answers', value: patient.totalLocated, caption: 'answers found' },
        { label: 'Missing answers', value: patient.totalMissing, caption: 'still pending' },
    ];

    return (
        <div className="min-h-screen bg-[#f5f5f7]">
            <header className="bg-white/80 backdrop-blur border-b border-slate-200 sticky top-0 z-20">
                <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
                    <div>
                        <button
                            onClick={() => navigate('/')}
                            className="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors mb-2"
                        >
                            ← Back to patient list
                        </button>
                        <h1 className="text-3xl font-semibold text-slate-900">
                            Patient {patient.id}
                        </h1>
                        <p className="text-sm text-slate-500 mt-1">
                            {formatDateRange(patient.startDate, patient.endDate)}
                        </p>
                    </div>
                    <div className="text-right text-sm text-slate-500">
                        <p>{patient.totalDocuments} total documents</p>
                        <p>{patient.relevantDocuments} relevant</p>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-4 py-8">
                <div className="flex flex-col lg:flex-row gap-8">
                    <div className="hidden lg:block lg:w-48 flex-shrink-0">
                        <div className="sticky top-32 space-y-4">
                            <div className="bg-white rounded-2xl border border-slate-200/70 shadow-sm p-4">
                                <ColorFilter
                                    questions={patient.questions}
                                    selectedColors={selectedColors}
                                    onToggleColor={handleToggleColor}
                                    onClear={() => setSelectedColors([])}
                                    compact
                                    label="Highlight"
                                />
                            </div>
                            <div className="bg-white rounded-2xl border border-slate-200/70 shadow-sm p-4">
                                <ColorFilter
                                    documentTypes={documentTypes}
                                    selectedTypes={selectedTypes}
                                    onToggleType={handleToggleType}
                                    onClearTypes={() => setSelectedTypes([])}
                                    compact
                                    isTypeFilter
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 space-y-6">
                        <section className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-8 space-y-6">
                            <div className="space-y-2">
                                <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                                    Patient summary
                                </p>
                                <h2 className="text-2xl font-semibold text-slate-900">
                                    Executive snapshot
                                </h2>
                            </div>
                            <p className="text-slate-600 leading-relaxed">{patient.summary}</p>
                            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                                {summaryStats.map((item) => (
                                    <div
                                        key={item.label}
                                        className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4"
                                    >
                                        <p className="text-xs uppercase tracking-wide text-slate-500">
                                            {item.label}
                                        </p>
                                        <p className="text-2xl font-semibold text-slate-900 mt-2">
                                            {item.value}
                                        </p>
                                        <p className="text-xs text-slate-500">{item.caption}</p>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section className="space-y-4">
                            <div className="flex items-center justify-between flex-wrap gap-2">
                                <div>
                                    <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
                                        Medical documents
                                    </p>
                                    <h3 className="text-xl font-semibold text-slate-900">
                                        Timeline of notes
                                    </h3>
                                </div>
                                {selectedTypes.length > 0 && (
                                    <span className="text-sm text-slate-500">
                                        Showing {filteredDocuments.length}{' '}
                                        {filteredDocuments.length === 1 ? 'document' : 'documents'}
                                    </span>
                                )}
                            </div>

                            {filteredDocuments.length > 0 ? (
                                filteredDocuments.map((doc, index) => {
                                    const previousDoc = index > 0 ? filteredDocuments[index - 1] : null;
                                    return (
                                        <div
                                            key={doc.id}
                                            ref={(el) => (documentRefs.current[doc.id] = el)}
                                            data-doc-id={doc.id}
                                        >
                                            <DocumentCard
                                                document={doc}
                                                index={index + 1}
                                                previousDate={previousDoc?.date}
                                                selectedColors={selectedColors}
                                            />
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="bg-white rounded-3xl border border-slate-200/70 shadow-sm p-10 text-center">
                                    <p className="text-slate-500">
                                        No documents match the selected filters.
                                    </p>
                                </div>
                            )}
                        </section>
                    </div>

                    <div className="lg:w-24 lg:block flex-shrink-0">
                        <Timeline
                            documents={filteredDocuments}
                            onDocumentClick={handleDocumentClick}
                            currentDate={currentDocumentDate}
                            selectedColors={selectedColors}
                            significantEvents={[]}
                        />
                    </div>
                </div>
            </main>
        </div>
    );
};

export default PatientInformation;

