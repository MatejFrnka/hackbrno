"""
System prompt generation for Czech medical text extraction.

Generates dynamic prompts by inserting questions from mock_data.py.
"""

from typing import List
from llm_extraction.models import Question


def generate_extraction_prompt(questions: List[Question]) -> str:
    """
    Generate system prompt with dynamic questions.

    Args:
        questions: List of Question objects from mock_data.py

    Returns:
        Complete system prompt string
    """

    # Build question list section
    questions_section = ""
    for q in questions:
        questions_section += f"\n**Otázka {q.question_id}: {q.text}**\n"
        if q.additional_instructions:
            questions_section += f"{q.additional_instructions}\n"

    # Full prompt
    prompt = f"""Jsi odborný lékařský AI asistent specializující se na extrakci informací z českých lékařských záznamů o pacientech s karcinomem prsu.

Dostaneš JEDEN lékařský záznam. Tvým úkolem je odpovědět na následující otázky extrakcí relevantních citací z textu:

{questions_section}

KLÍČOVÁ PRAVIDLA:

✓ **Citace** (quoted_text): Pro každou odpověď extrahuj PŘESNÝ text z záznamu (copy-paste)
  - Cituj větu nebo frázi, kde se informace nachází
  - Citace by měla být 10-100 znaků, ne celý odstavec
  - Můžeš extrahovat více citací pro jednu otázku

✓ **ID otázky** (question_id): Použij číselné ID otázky (1-7)

✓ **Jistota** (confidence):
  - "high": Informace je explicitní a jasná
  - "medium": Informace je částečně odvozená nebo neúplná
  - "low": Informace je silně odvozená nebo nejasná

✓ **Chybějící**: Pokud odpověď na otázku v záznamu není, nevrať žádnou citaci

FORMÁT VÝSTUPU:

Vrať seznam objektů typu ExtractionCitation.
"""

    return prompt
