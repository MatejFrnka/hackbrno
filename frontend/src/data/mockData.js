// Mock data for the patient management system
import { hack01 } from './hack01.js';

// Common medical questions with assigned colors
export const questions = [
    { id: 'q1', text: 'What is the TNM code?', color: 'blue' },
    { id: 'q2', text: 'What is the diagnosis?', color: 'red' },
    { id: 'q3', text: 'What is the treatment plan?', color: 'green' },
    { id: 'q4', text: 'What are the symptoms?', color: 'yellow' },
    { id: 'q5', text: 'What is the prognosis?', color: 'purple' },
    { id: 'q6', text: 'What medications are prescribed?', color: 'orange' },
    { id: 'q7', text: 'What are the test results?', color: 'pink' },
    { id: 'q8', text: 'What is the patient history?', color: 'cyan' },
];

// Helper function to generate random date within range
const randomDate = (start, end) => {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const randomTime = startTime + Math.random() * (endTime - startTime);
    return new Date(randomTime).toISOString().split('T')[0];
};

// Helper function to create highlighted text
const createHighlightedText = (text, highlights) => {
    let result = [];
    let lastIndex = 0;

    highlights.sort((a, b) => a.start - b.start);

    highlights.forEach((highlight) => {
        if (highlight.start > lastIndex) {
            result.push({ type: 'text', content: text.substring(lastIndex, highlight.start) });
        }
        result.push({
            type: 'highlight',
            content: text.substring(highlight.start, highlight.end),
            color: highlight.color,
        });
        lastIndex = highlight.end;
    });

    if (lastIndex < text.length) {
        result.push({ type: 'text', content: text.substring(lastIndex) });
    }

    return result.length > 0 ? result : [{ type: 'text', content: text }];
};

// Generate mock documents for a patient
const generateDocuments = (patientId, startDate, endDate, questionColors) => {
    const documentCount = Math.floor(Math.random() * 30) + 10;
    const documents = [];

    // Extract texts from hack01 data
    const sampleTexts = hack01.dokumentace.pacient.zaznam.map(record => record.text);

    for (let i = 0; i < documentCount; i++) {
        const date = randomDate(startDate, endDate);
        const textIndex = Math.floor(Math.random() * sampleTexts.length);
        let text = sampleTexts[textIndex];

        // Add random highlights based on available question colors
        const highlights = [];
        const numHighlights = Math.floor(Math.random() * 3) + 1;
        const availableColors = [...questionColors];

        for (let j = 0; j < numHighlights && availableColors.length > 0; j++) {
            const colorIndex = Math.floor(Math.random() * availableColors.length);
            const color = availableColors[colorIndex];
            availableColors.splice(colorIndex, 1);

            // Find a phrase to highlight (Czech medical terms from hack01)
            const phrases = {
                blue: ['cT2N0M0', 'pT2N0M0', 'pTNM', 'TNM', 'klasifikace'],
                red: ['diagnóza', 'prsu', 'karcinom', 'invazivní karcinom', 'malignita'],
                green: ['léčba', 'Léčba', 'radioterapie', 'operace', 'mastektomie', 'léčebná rozvaha'],
                yellow: ['potíže', 'Potíže', 'bolesti', 'bolest', 'únavu', 'symptomy'],
                purple: ['prognóza', 'Prognóza', 'příznivé', 'pozitivní', 'CT', 'Osobní'],
                orange: ['medikace', 'Medikace', 'léky', 'léčiv', 'farmakologická anamnéza'],
                pink: ['vyšetření', 'Vyšetření', 'výsledky', 'laboratorní', 'CT', 'RTG', 'UZ'],
                cyan: ['anamnéza', 'Anamnéza', 'osobní anamnéza', 'rodinná anamnéza', 'historie'],
            };

            const colorPhrases = phrases[color] || [];
            if (colorPhrases.length > 0) {
                const phrase = colorPhrases[Math.floor(Math.random() * colorPhrases.length)];
                const start = text.indexOf(phrase);
                if (start !== -1) {
                    highlights.push({
                        start,
                        end: start + phrase.length,
                        color,
                    });
                }
            }
        }

        documents.push({
            id: `doc-${patientId}-${i}`,
            date,
            text,
            highlightedText: createHighlightedText(text, highlights),
            highlights,
        });
    }

    return documents.sort((a, b) => new Date(a.date) - new Date(b.date));
};

// Generate mock patients
export const generatePatients = () => {
    const patients = [];
    const patientIds = [
        '000129/0190',
        '000245/0191',
        '000312/0192',
        '000478/0193',
        '000521/0194',
        '000689/0195',
        '000734/0196',
        '000856/0197',
        '000912/0198',
        '001045/0199',
    ];

    const summaries = [
        'Patient with a complex chronic condition that necessitates continuous monitoring, frequent adjustments to treatment regimens, and a comprehensive approach to care involving multiple healthcare professionals. This patient has a longstanding medical history characterized by episodic symptom flare-ups, laboratory findings that require careful interpretation, and a medication regimen that includes both mainstay and adjunctive therapies. ',
        'Post-operative follow-up case with regular check-ups and imaging studies.',
        'Oncology patient undergoing treatment with multiple specialists involved.',
        'Cardiac patient with history of interventions, stable on current regimen.',
        'Endocrine disorder managed with medication and lifestyle modifications.',
        'Respiratory condition with periodic exacerbations requiring careful management.',
        'Neurological case with progressive symptoms under specialist care.',
        'Gastrointestinal disorder with dietary restrictions and medication therapy.',
        'Rheumatological condition with joint involvement and systemic symptoms.',
        'Hematological disorder requiring regular monitoring and treatment adjustments.',
    ];

    patientIds.forEach((id, index) => {
        const startYear = 2000 + Math.floor(Math.random() * 5);
        const endYear = 2020 + Math.floor(Math.random() * 4);
        const startDate = `${startYear}-01-01`;
        const endDate = `${endYear}-12-31`;

        // Assign some questions to this patient
        const numQuestions = Math.floor(Math.random() * 5) + 3;
        const patientQuestions = questions.slice(0, numQuestions);
        const questionColors = patientQuestions.map(q => q.color);

        // Generate documents
        const allDocuments = generateDocuments(id, startDate, endDate, questionColors);
        const totalDocuments = allDocuments.length;
        const relevantDocuments = Math.floor(totalDocuments * (0.6 + Math.random() * 0.3));

        // Calculate answer statistics
        const locatedAnswers = {};
        const missingAnswers = {};

        patientQuestions.forEach((q) => {
            const documentsWithAnswer = allDocuments.filter(doc =>
                doc.highlights.some(h => h.color === q.color)
            ).length;
            locatedAnswers[q.color] = documentsWithAnswer;
            missingAnswers[q.color] = relevantDocuments - documentsWithAnswer;
        });

        const totalLocated = Object.values(locatedAnswers).reduce((a, b) => a + b, 0);
        const totalMissing = Object.values(missingAnswers).reduce((a, b) => a + b, 0);

        // Determine difficulty (1-5)
        const difficulty = Math.floor(Math.random() * 5) + 1;

        // Determine data amount category
        let dataAmount = 'small';
        if (totalDocuments > 25) dataAmount = 'large';
        else if (totalDocuments > 15) dataAmount = 'medium';

        patients.push({
            id,
            startDate,
            endDate,
            totalDocuments,
            relevantDocuments,
            locatedAnswers,
            missingAnswers,
            totalLocated,
            totalMissing,
            summary: summaries[index],
            difficulty,
            dataAmount,
            questions: patientQuestions,
            documents: allDocuments,
        });
    });

    return patients;
};

export const patients = generatePatients();

// Calculate executive summary statistics
export const getExecutiveSummary = () => {
    const totalPatients = patients.length;
    const totalPages = patients.reduce((sum, p) => sum + p.totalDocuments, 0);
    const relevantPages = patients.reduce((sum, p) => sum + p.relevantDocuments, 0);
    const totalMissing = patients.reduce((sum, p) => sum + p.totalMissing, 0);

    const dataAmountBreakdown = {
        large: patients.filter(p => p.dataAmount === 'large').length,
        medium: patients.filter(p => p.dataAmount === 'medium').length,
        small: patients.filter(p => p.dataAmount === 'small').length,
    };

    return {
        totalPatients,
        totalPages,
        relevantPages,
        totalMissing,
        dataAmountBreakdown,
    };
};

