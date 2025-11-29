"""
Feature extraction using OpenAI with dynamic questions.
"""

import asyncio
import random
import typing
from typing import List
from openai import AsyncOpenAI

from llm_extraction.models import (
    PatientData,
    Question,
    ExtractionResult,
    ExtractionCitationWithSpan,
    HighlightCitationWithSpan,
    HighlightExtractionResult,
    FilteredHighlightsResult,
    MedicalRecord
)
from llm_extraction.prompts import (
    generate_extraction_prompt,
    generate_highlight_extraction_prompt,
    generate_highlight_filter_prompt,
    generate_patient_summary_prompt,
    generate_short_summary_prompt,
    generate_batch_summary_prompt
)

MAX_CONCURRENT_REQUESTS = 20  # Limit concurrent OpenAI requests


class FeatureExtractor:
    """Extract citations from medical records using LLM with dynamic questions"""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-5.1"):
        """
        Args:
            client: AsyncOpenAI client instance
            model: OpenAI model to use for extraction
        """
        self.client = client
        self.model = model

    async def _extract_single_record(
        self,
        record: MedicalRecord,
        system_prompt: str,
        idx: int,
        total: int,
        semaphore: asyncio.Semaphore
    ) -> dict:
        """
        Extract features from a single record asynchronously with retry logic.

        Args:
            record: Medical record to process
            system_prompt: System prompt with questions
            idx: Record index (for logging)
            total: Total number of records (for logging)
            semaphore: Semaphore to limit concurrent requests

        Returns:
            Dict with record_id and citations
        """
        # Add random jitter (0-0.5 seconds) before acquiring semaphore
        jitter = random.uniform(0, 0.5)
        await asyncio.sleep(jitter)

        async with semaphore:
            print(f"  Processing record {idx + 1}/{total}: {record.record_id} ({record.date})")

            # Format record for LLM
            user_message = f"""Record ID: {record.record_id}
Datum: {record.date}
Typ: {record.record_type}

{record.text}
"""

            max_retries = 3
            base_delay = 1.0  # Start with 1 second

            for attempt in range(max_retries):
                try:
                    # Call OpenAI with structured output
                    response = await self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        response_format=ExtractionResult,
                        temperature=0
                    )

                    result = response.choices[0].message.parsed

                    print(f"    → Extracted {len(result.citations)} citations")

                    return {
                        'record_id': record.record_id,
                        'citations': result.citations
                    }

                except Exception as e:
                    if attempt < max_retries - 1:
                        # Calculate exponential backoff delay: 1s, 2s, 4s
                        delay = base_delay * (2 ** attempt)
                        print(f"    WARNING: Attempt {attempt + 1}/{max_retries} failed for {record.record_id}: {e}")
                        print(f"    Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        print(f"    ERROR: All {max_retries} attempts failed for {record.record_id}: {e}")
                        return {
                            'record_id': record.record_id,
                            'citations': []
                        }

    async def extract_patient_features(
        self,
        patient_data: PatientData,
        questions: List[Question]
    ) -> List[dict]:
        """
        Extract features from all patient records asynchronously.

        Args:
            patient_data: Parsed patient data with medical records
            questions: List of questions to answer

        Returns:
            List of dicts: {'record_id': str, 'citations': List[ExtractionCitation]}
        """
        # Generate system prompt with questions
        system_prompt = generate_extraction_prompt(questions)

        print(f"Extracting features from {len(patient_data.records)} records...")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        # Create async tasks for all records
        tasks = [
            self._extract_single_record(record, system_prompt, idx, len(patient_data.records), semaphore)
            for idx, record in enumerate(patient_data.records)
        ]

        # Use as_completed to process results as they arrive
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

        return results


class HighlightExtractor:
    """Extract highlights from medical records using LLM"""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-5.1"):
        """
        Args:
            client: AsyncOpenAI client instance
            model: OpenAI model to use for extraction
        """
        self.client = client
        self.model = model

    async def _extract_single_record(
        self,
        record: MedicalRecord,
        system_prompt: str,
        idx: int,
        total: int,
        semaphore: asyncio.Semaphore
    ) -> dict:
        """
        Extract highlights from a single record asynchronously with retry logic.

        Args:
            record: Medical record to process
            system_prompt: System prompt for highlight extraction
            idx: Record index (for logging)
            total: Total number of records (for logging)
            semaphore: Semaphore to limit concurrent requests

        Returns:
            Dict with record_id, record_date, record_type, and highlights
        """
        # Add random jitter (0-0.5 seconds) before acquiring semaphore
        jitter = random.uniform(0, 0.5)
        await asyncio.sleep(jitter)

        async with semaphore:
            print(f"  Processing record {idx + 1}/{total}: {record.record_id} ({record.date})")

            # Format record for LLM
            user_message = f"""Record ID: {record.record_id}
Datum: {record.date}
Typ: {record.record_type}

{record.text}
"""

            max_retries = 3
            base_delay = 1.0  # Start with 1 second

            for attempt in range(max_retries):
                try:
                    # Call OpenAI with structured output
                    response = await self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        response_format=HighlightExtractionResult,
                        temperature=0
                    )

                    result = response.choices[0].message.parsed

                    print(f"    → Extracted {len(result.highlights)} highlights")

                    return {
                        'record_id': record.record_id,
                        'record_date': record.date,
                        'record_type': record.record_type,
                        'highlights': result.highlights
                    }

                except Exception as e:
                    if attempt < max_retries - 1:
                        # Calculate exponential backoff delay: 1s, 2s, 4s
                        delay = base_delay * (2 ** attempt)
                        print(f"    WARNING: Attempt {attempt + 1}/{max_retries} failed for {record.record_id}: {e}")
                        print(f"    Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        print(f"    ERROR: All {max_retries} attempts failed for {record.record_id}: {e}")
                        return {
                            'record_id': record.record_id,
                            'record_date': record.date,
                            'record_type': record.record_type,
                            'highlights': []
                        }

    async def extract_highlights(
        self,
        patient_data: PatientData
    ) -> List[dict]:
        """
        Extract highlights from all patient records asynchronously (Stage 1).

        Args:
            patient_data: Parsed patient data with medical records

        Returns:
            List of dicts: {
                'record_id': int,
                'record_date': str,
                'record_type': str,
                'highlights': List[HighlightCitation]
            }
        """
        # Generate system prompt
        system_prompt = generate_highlight_extraction_prompt()

        print(f"Extracting highlights from {len(patient_data.records)} records...")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        # Create async tasks for all records
        tasks = [
            self._extract_single_record(record, system_prompt, idx, len(patient_data.records), semaphore)
            for idx, record in enumerate(patient_data.records)
        ]

        # Use as_completed to process results as they arrive
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

        return results


class HighlightFilter:
    """Filter highlights to most important medical events using LLM"""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-5.1"):
        """
        Args:
            client: AsyncOpenAI client instance
            model: OpenAI model to use for filtering
        """
        self.client = client
        self.model = model

    async def filter_highlights(
        self,
        highlights_with_spans: List[HighlightCitationWithSpan],
        patient_data: PatientData
    ) -> List[HighlightCitationWithSpan]:
        """
        Filter highlights to only the most important medical events (Stage 2).

        Makes ONE LLM call with ALL highlights and returns filtered subset.

        Args:
            highlights_with_spans: All highlights with span information
            patient_data: Patient data (needed for record metadata)

        Returns:
            Filtered list of HighlightCitationWithSpan (only important ones)
        """
        if not highlights_with_spans:
            print("No highlights to filter")
            return []

        print(f"Filtering {len(highlights_with_spans)} highlights...")

        # Build record lookup for metadata
        record_lookup = {r.record_id: r for r in patient_data.records}

        # Sort highlights by date (chronological order)
        sorted_highlights = sorted(
            highlights_with_spans,
            key=lambda h: record_lookup[h.record_id].date
        )

        # Build context list for LLM
        highlights_with_context = []
        for h in sorted_highlights:
            record = record_lookup[h.record_id]
            highlights_with_context.append({
                "index": len(highlights_with_context),  # 0-based index
                "quoted_text": h.quoted_text,
                "note": h.note,
                "record_id": h.record_id,
                "record_date": record.date,
                "record_type": record.record_type
            })

        # Generate system prompt
        system_prompt = generate_highlight_filter_prompt()

        # Format user message with all highlights
        user_message = self._format_highlights_for_filtering(highlights_with_context)

        # Call LLM with structured output
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format=FilteredHighlightsResult,
                    temperature=0
                )

                result = response.choices[0].message.parsed

                # Extract selected highlights by indices
                selected_indices = set(result.selected_highlights)
                filtered_highlights = [
                    sorted_highlights[i]
                    for i in selected_indices
                    if 0 <= i < len(sorted_highlights)
                ]

                print(f"  → Selected {len(filtered_highlights)}/{len(sorted_highlights)} highlights")
                print(f"  → Reasoning: {result.reasoning}")

                return filtered_highlights

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"  WARNING: Attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"  Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ERROR: All {max_retries} attempts failed: {e}")
                    # On failure, return all highlights (no filtering)
                    print(f"  → Returning all {len(sorted_highlights)} highlights (no filtering)")
                    return sorted_highlights

    def _format_highlights_for_filtering(self, highlights_with_context: List[dict]) -> str:
        """
        Format highlights for LLM filtering.

        Args:
            highlights_with_context: List of highlight dicts with metadata

        Returns:
            Formatted string for LLM
        """
        lines = ["Zde je seznam všech highlights z dokumentace pacienta:\n"]

        for h in highlights_with_context:
            lines.append(f"[{h['index']}] Datum: {h['record_date']} | Typ: {h['record_type']} | Record ID: {h['record_id']}")
            lines.append(f"    Citace: \"{h['quoted_text']}\"")
            lines.append(f"    Poznámka: {h['note']}")
            lines.append("")

        lines.append(f"\nCelkem: {len(highlights_with_context)} highlights")
        lines.append("\nVyber indexy highlights, které jsou skutečně důležité.")

        return "\n".join(lines)


class PatientSummaryExtractor:
    """
    Extracts a comprehensive narrative summary of a patient's medical journey.
    """

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-5.1"):
        """
        Args:
            client: AsyncOpenAI client instance
            model: OpenAI model to use for summarization
        """
        self.client = client
        self.model = model

    async def summarize_patient_async(self, patient_data: PatientData) -> str:
        """
        Generate patient summary asynchronously using LLM.

        Args:
            patient_data: PatientData object containing medical records

        Returns:
            String containing narrative summary of patient journey
        """
        system_prompt = generate_patient_summary_prompt()

        user_prompt = f"""Níže jsou lékařské záznamy pacienta s karcinomem prsu:\n\n{chr(10).join([f'Záznam ID: {record.record_id}\nDatum: {record.date}\nTyp záznamu: {record.record_type}\nText záznamu:\n{record.text}\n' for record in patient_data.records])}"""

        print("Generating patient summary...")

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                )

                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"  WARNING: Attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"  Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ERROR: All {max_retries} attempts failed: {e}")
                    raise

    async def summarize_citations_async(
        self,
        citations_with_spans: List[ExtractionCitationWithSpan],
        questions: List[Question],
        patient_data: PatientData
    ) -> str:
        """
        Generate short summary based on extracted citations.

        Creates a concise summary (4-6 sentences) focused on findings from
        citation extraction. Returns empty string if no citations exist.

        Args:
            citations_with_spans: List of ExtractionCitationWithSpan objects
            questions: List of Question objects used for extraction
            patient_data: PatientData object (for record metadata)

        Returns:
            String containing concise summary, or empty string if no citations
        """
        # Early return if no citations (skip LLM call)
        if not citations_with_spans:
            print("  No citations to summarize, returning empty string")
            return ""

        # Generate system prompt with questions
        system_prompt = generate_short_summary_prompt(questions)

        # Build record lookup for metadata
        record_lookup = {r.record_id: r for r in patient_data.records}

        # Group citations by question_id
        citations_by_question = {}
        for citation in citations_with_spans:
            qid = citation.question_id
            if qid not in citations_by_question:
                citations_by_question[qid] = []
            citations_by_question[qid].append(citation)

        # Build question lookup
        question_lookup = {q.question_id: q for q in questions}

        # Format citations for LLM
        user_message_lines = ["Zde jsou extrahované citace z dokumentace pacientky:\n"]

        # Add citations grouped by question
        for qid in sorted(citations_by_question.keys()):
            question = question_lookup.get(qid)
            citations = citations_by_question[qid]

            if question:
                user_message_lines.append(f"\n**Otázka {qid}: {question.text}**")
                user_message_lines.append(f"Počet citací: {len(citations)}\n")

            for idx, citation in enumerate(citations, 1):
                record = record_lookup.get(citation.record_id)
                if record:
                    user_message_lines.append(
                        f"  [{idx}] Datum: {record.date} | Record ID: {citation.record_id} | Confidence: {citation.confidence}"
                    )
                user_message_lines.append(f"      Citace: \"{citation.quoted_text}\"\n")

        # Add questions without citations
        questions_with_citations = set(citations_by_question.keys())
        all_question_ids = {q.question_id for q in questions}
        missing_question_ids = all_question_ids - questions_with_citations

        if missing_question_ids:
            user_message_lines.append("\n**Otázky BEZ citací (žádné nálezy):**")
            for qid in sorted(missing_question_ids):
                question = question_lookup.get(qid)
                if question:
                    user_message_lines.append(f"- Otázka {qid}: {question.text}")

        user_message_lines.append(f"\n\nCelkem: {len(citations_with_spans)} citací pro {len(citations_by_question)}/{len(questions)} otázek")
        user_message_lines.append("Vytvoř krátké shrnutí (4-6 vět) se zaměřením na medicínsky nejdůležitější nálezy. Zmiň také otázky bez nálezů.")

        user_message = "\n".join(user_message_lines)

        print("Generating short summary from citations...")

        # Retry logic (consistent with other methods)
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1,
                )

                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"  WARNING: Attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"  Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ERROR: All {max_retries} attempts failed: {e}")
                    raise


class BatchSummaryExtractor:
    """
    Extracts a comprehensive summary across multiple patients for cohort-level overview.
    """

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-5.1"):
        """
        Args:
            client: AsyncOpenAI client instance
            model: OpenAI model to use for summarization
        """
        self.client = client
        self.model = model

    async def summarize_batch_async(self, patient_summaries: typing.List[typing.Tuple[str, str]]) -> str:
        """
        Generate batch summary asynchronously using LLM.

        Args:
            patient_summaries: List of (patient_id, summary) tuples

        Returns:
            String containing narrative summary of entire patient cohort
        """
        system_prompt = generate_batch_summary_prompt()

        # Format patient summaries for LLM
        user_prompt_lines = ["Zde jsou individuální sumáře pacientek:\n"]
        for idx, (patient_id, summary) in enumerate(patient_summaries, 1):
            user_prompt_lines.append(f"{idx}. Pacientka {patient_id}:")
            user_prompt_lines.append(f"{summary}\n")

        user_prompt = "\n".join(user_prompt_lines)

        print(f"Generating batch summary for {len(patient_summaries)} patients...")

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                )

                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"  WARNING: Attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"  Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ERROR: All {max_retries} attempts failed: {e}")
                    raise
