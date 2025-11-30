const API_BASE_URL = 'http://localhost:5001';

// Lighten a hex color by blending it with white
const lightenHexColor = (hex, factor = 0.6) => {
    if (!hex || !hex.startsWith('#')) return hex;

    // Remove # and parse RGB
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    // Blend with white (255, 255, 255)
    const newR = Math.round(r + (255 - r) * factor);
    const newG = Math.round(g + (255 - g) * factor);
    const newB = Math.round(b + (255 - b) * factor);

    // Convert back to hex
    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
};

const createHighlightedText = (text, highlights, questions) => {
    if (!highlights || highlights.length === 0) {
        return [{ type: 'text', content: text }];
    }

    // Create a map of question_id to color (lightened)
    const questionColorMap = {};
    questions.forEach(q => {
        questionColorMap[q.id] = lightenHexColor(q.rgb_color);
    });

    // Sort highlights by start offset
    const sortedHighlights = [...highlights].sort((a, b) => a.offset_start - b.offset_start);

    let result = [];
    let lastIndex = 0;

    sortedHighlights.forEach((highlight) => {
        if (highlight.offset_start > lastIndex) {
            result.push({
                type: 'text',
                content: text.substring(lastIndex, highlight.offset_start)
            });
        }
        result.push({
            type: 'highlight',
            content: text.substring(highlight.offset_start, highlight.offset_end),
            color: questionColorMap[highlight.question_id] || null,
            questionId: highlight.question_id,
        });
        lastIndex = highlight.offset_end;
    });

    if (lastIndex < text.length) {
        result.push({ type: 'text', content: text.substring(lastIndex) });
    }

    return result.length > 0 ? result : [{ type: 'text', content: text }];
};

// Fetch dashboard data
export const fetchDashboard = async () => {
    const response = await fetch(`${API_BASE_URL}/api/dashboard`);
    if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
    }
    const data = await response.json();
    console.log("aaa");
    console.log(data);
    // Transform data to match frontend expectations
    const transformedPatients = data.patients.map((p) => {
        // Combine answered and unanswered questions
        const allQuestions = [...p.answered_questions, ...p.unanswered_questions];
        // Create questions array with color names
        const questions = allQuestions.map((q) => ({
            id: q.id,
            text: q.name,
            color: q.rgb_color,
        }));

        // Use patient_id if available, otherwise use id as fallback
        // Note: patient_id is the string identifier, id is the database ID
        return {
            id: p.id,
            name: p.name,
            startDate: p.documents_start_date,
            endDate: p.documents_end_date,
            totalDocuments: p.documents_total,
            relevantDocuments: p.relevant_documents_total,
            locatedAnswers: p.answered_questions,
            missingAnswers: p.unanswered_questions,
            totalMissing: 0,
            summary: p.short_summary || '',
            difficulty: p.difficulty || 1,
            questions,
        };
    });

    // Calculate executive summary
    const totalPatients = transformedPatients.length;
    const totalPages = transformedPatients.reduce((sum, p) => sum + p.totalDocuments, 0);
    const relevantPages = transformedPatients.reduce((sum, p) => sum + p.relevantDocuments, 0);
    const totalMissing = transformedPatients.reduce((sum, p) => sum + p.totalMissing, 0);

    return {
        summary: data.summary || '',
        totalPatients,
        totalPages,
        relevantPages,
        totalMissing,
        patients: transformedPatients,
    };
};

// Fetch patient data
export const fetchPatient = async (patientId) => {
    const response = await fetch(`${API_BASE_URL}/api/patient/${encodeURIComponent(patientId)}`);
    if (!response.ok) {
        if (response.status === 404) {
            return null;
        }
        throw new Error('Failed to fetch patient data');
    }
    const data = await response.json();
    // Transform questions
    const questions = (data.questions_types || []).map((q) => ({
        id: q.id,
        text: q.name,
        color: q.rgb_color,
    }));

    // Transform documents
    const documents = (data.documents || []).map((doc) => {
        const highlightedText = createHighlightedText(
            doc.text,
            doc.highlights || [],
            data.questions_types || []
        );

        // Extract highlights for timeline
        const highlights = (doc.highlights || []).map((h) => {
            const question = (data.questions_types || []).find(q => q.id === h.question_id);
            return {
                start: h.offset_start,
                end: h.offset_end,
                color: question ? question.rgb_color : 'slate',
                question_id: h.question_id,
                confidence: h.confidence,
            };
        });

        // Extract commented highlights for timeline
        const commentedHighlights = (doc.commented_highlights || []).map((h, idx) => ({
            id: `commented-${doc.id}-${idx}`,
            date: doc.date,
            description: h.description,
            color: '#cbd5e1', // gray
        }));

        return {
            id: doc.id.toString(),
            date: doc.date,
            typ: doc.type,
            text: doc.text,
            highlightedText,
            highlights,
            commentedHighlights: commentedHighlights,
        };
    });

    let answeredQuestionsIds = documents.reduce((set, d) => {
        d.highlights.reduce((sett, h) => { sett.add(h.question_id); return sett; }, set);
        return set;
    }, new Set());

    return {
        id: patientId,
        name: data.name,
        summary: data.long_summary || '',
        questions,
        documents,
        totalDocuments: documents.length,
        relevantDocuments: documents.filter(d => d.highlights.length > 0).length,
        totalLocated: answeredQuestionsIds.size,
        totalMissing: questions.length - answeredQuestionsIds.size,
        answeredQuestions: answeredQuestionsIds,
    };
};

