const API_BASE_URL = 'http://localhost:5000';

// Convert RGB color to color name
const rgbToColorName = (rgbColor) => {
    if (!rgbColor) return 'slate';
    
    // Parse RGB color (format: "rgb(59, 130, 246)" or "#3b82f6")
    let r, g, b;
    if (rgbColor.startsWith('#')) {
        r = parseInt(rgbColor.slice(1, 3), 16);
        g = parseInt(rgbColor.slice(3, 5), 16);
        b = parseInt(rgbColor.slice(5, 7), 16);
    } else if (rgbColor.startsWith('rgb')) {
        const matches = rgbColor.match(/\d+/g);
        if (matches) {
            r = parseInt(matches[0]);
            g = parseInt(matches[1]);
            b = parseInt(matches[2]);
        }
    } else {
        return 'slate';
    }
    
    // Map RGB values to color names (approximate)
    // Blue: rgb(59, 130, 246) or similar
    if (b > r && b > g) return 'blue';
    // Red: rgb(239, 68, 68) or similar
    if (r > g && r > b && r > 150) return 'red';
    // Green: rgb(34, 197, 94) or similar
    if (g > r && g > b && g > 100) return 'green';
    // Yellow: rgb(234, 179, 8) or similar
    if (r > 200 && g > 150 && b < 100) return 'yellow';
    // Purple: rgb(168, 85, 247) or similar
    if (r > 100 && b > 150 && g < 100) return 'purple';
    // Orange: rgb(249, 115, 22) or similar
    if (r > 200 && g > 100 && b < 100) return 'orange';
    // Pink: rgb(236, 72, 153) or similar
    if (r > 200 && g < 100 && b > 100) return 'pink';
    // Cyan: rgb(6, 182, 212) or similar
    if (g > 150 && b > 150 && r < 100) return 'cyan';
    
    return 'slate';
};

// Create highlighted text from document text and highlights
const createHighlightedText = (text, highlights, questions) => {
    if (!highlights || highlights.length === 0) {
        return [{ type: 'text', content: text }];
    }
    
    // Create a map of question_id to color
    const questionColorMap = {};
    questions.forEach(q => {
        questionColorMap[q.id] = rgbToColorName(q.rgb_color);
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
        const color = questionColorMap[highlight.question_id] || 'slate';
        result.push({
            type: 'highlight',
            content: text.substring(highlight.offset_start, highlight.offset_end),
            color: color,
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
    
    // Transform data to match frontend expectations
    const transformedPatients = data.patients.map((p) => {
        // Combine answered and unanswered questions
        const allQuestions = [...p.answered_questions, ...p.unanswered_questions];
        
        // Create questions array with color names
        const questions = allQuestions.map((q) => ({
            id: q.id,
            text: q.description,
            color: rgbToColorName(q.rgb_color),
        }));
        
        // Calculate located and missing answers
        const locatedAnswers = {};
        const missingAnswers = {};
        
        p.answered_questions.forEach((q) => {
            const color = rgbToColorName(q.rgb_color);
            locatedAnswers[color] = q.documents_count || 0;
        });
        
        p.unanswered_questions.forEach((q) => {
            const color = rgbToColorName(q.rgb_color);
            missingAnswers[color] = 0;
        });
        
        const totalLocated = Object.values(locatedAnswers).reduce((a, b) => a + b, 0);
        const totalMissing = p.unanswered_questions.length;
        
        // Use patient_id if available, otherwise use id as fallback
        // Note: patient_id is the string identifier, id is the database ID
        const patientId = p.patient_id || String(p.id || '');
        
        return {
            id: patientId,
            startDate: p.documents_start_date,
            endDate: p.documents_end_date,
            totalDocuments: p.documents_total,
            relevantDocuments: p.relevant_documents_total,
            locatedAnswers,
            missingAnswers,
            totalLocated,
            totalMissing,
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
        text: q.description,
        color: rgbToColorName(q.rgb_color),
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
                color: question ? rgbToColorName(question.rgb_color) : 'slate',
            };
        });
        
        return {
            id: doc.id.toString(),
            date: doc.date,
            typ: doc.type,
            text: doc.text,
            highlightedText,
            highlights,
        };
    });
    
    return {
        id: patientId,
        summary: data.long_summary || '',
        questions,
        documents,
        totalDocuments: documents.length,
        relevantDocuments: documents.filter(d => d.highlights.length > 0).length,
        totalLocated: documents.reduce((sum, d) => sum + d.highlights.length, 0),
        totalMissing: 0, // Calculate based on unanswered questions if needed
    };
};

