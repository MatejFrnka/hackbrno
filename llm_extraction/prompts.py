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


def generate_highlight_extraction_prompt() -> str:
    """
    Generate system prompt for extracting highlights from individual medical records.

    This prompt is designed to identify significant medical events in a single record
    that should be highlighted for quick review.

    Returns:
        Complete system prompt string in Czech
    """

    prompt = """Jsi odborný lékařský AI asistent specializující se na analýzu českých lékařských záznamů o pacientech s karcinomem prsu.

Dostaneš JEDEN lékařský záznam. Tvým úkolem je identifikovat důležité medicínské události nebo informace, které by měly být zvýrazněny (highlighted) pro rychlý přehled.

CO EXTRAHOVAT jako highlights:

✓ **Nové nálezy**:
  - Nově diagnostikované nemoci nebo stavy
  - Nové metastázy nebo progrese onemocnění
  - Nové komplikace

✓ **Významné změny ve stavu pacienta**:
  - Zhoršení nebo zlepšení klinického stavu
  - Změny v mobilitě, symptomech
  - Nové nebo měnící se bolesti

✓ **Důležité výkony a vyšetření**:
  - Operace a chirurgické zákroky
  - Biopsie a histologická vyšetření
  - Zobrazovací vyšetření s významnými nálezy
  - Změny v léčebném plánu

✓ **Kritické laboratorní nebo diagnostické nálezy**:
  - TNM klasifikace
  - Hormonální receptory (ER, PR, HER2)
  - Patologické laboratorní hodnoty (např. hyperkalcémie)

CO NEEXTRAHOVAT:

✗ Rutinní kontroly bez nových nálezů
✗ Opakované informace bez změny
✗ Obecné popisy bez konkrétních nálezů
✗ Administrativní informace

FORMÁT KAŽDÉHO HIGHLIGHT:

1. **quoted_text**: PŘESNÝ text z záznamu (10-150 znaků)
   - Cituj konkrétní část textu, kde se informace nachází
   - Musí být doslovná citace (copy-paste)

2. **note**: Tvoje vysvětlení (20-200 znaků)
   - Proč je toto důležité?
   - Co to znamená pro pacienta?
   - Stručně, jasně, odborně

DŮLEŽITÉ POZNÁMKY:

- Pokud záznam NEOBSAHUJE žádné významné události, vrať prázdný seznam highlights
- Není nutné zvýrazňovat každý záznam - pouze ty se skutečně významnými informacemi
- Zaměř se na NOVÉ nebo ZMĚNĚNÉ informace, ne na opakování

PŘÍKLADY:

Záznam: "První onkologická konzultace pro nově diagnostikovaný karcinom levého prsu..."
→ Highlight:
  quoted_text: "nově diagnostikovaný karcinom levého prsu"
  note: "První diagnóza karcinomu prsu, zahájení onkologické péče"

Záznam: "Onkologická kontrola v průběhu paliativní systémové léčby... Fyzikálně celkově kardiopulmonálně kompenzovaná, lokálně v prsu stacionární rozsah tumoru..."
→ BEZ HIGHLIGHT (rutinní kontrola bez změn)

Záznam: "Provedena hydratace intravenózními infuzemi, podán redukovaný bolus bisfosfonátu vzhledem k monoledvině. Kalcémie po terapii klesá..."
→ Highlight:
  quoted_text: "asymptomatickou hyperkalcémii... Kalcémie po terapii klesá"
  note: "Akutní léčba hyperkalcémie s pozitivní odpovědí"

VÝSTUP:

Vrať seznam objektů typu HighlightCitation.
Pokud nejsou žádné významné události, vrať prázdný seznam.
"""

    return prompt


def generate_highlight_filter_prompt() -> str:
    """
    Generate system prompt for filtering highlights to most important ones.

    This prompt receives ALL highlights from all records and must select only
    the truly significant medical events.

    Returns:
        Complete system prompt string in Czech
    """

    prompt = """Jsi odborný lékařský AI asistent specializující se na analýzu českých lékařských záznamů o pacientech s karcinomem prsu.

Dostaneš SEZNAM VŠECH highlights z celé zdravotnické dokumentace jednoho pacienta. Tvým úkolem je vybrat pouze SKUTEČNĚ DŮLEŽITÉ události, které by měly být zvýrazněny pro rychlý přehled.

KRITÉRIA PRO VÝBĚR:

✓ **Zachovat**:
  - První diagnóza karcinomu
  - Nové metastázy nebo progrese
  - Významné změny v léčbě (zahájení, změna režimu, ukončení)
  - Důležité operace a výkony
  - Kritické komplikace (infekce, toxicita, hospitalizace)
  - Významné změny ve stavu pacienta
  - První výskyt TNM klasifikace nebo hormonálních receptorů
  - Recidiva onemocnění

✗ **Odstranit**:
  - Opakované rutinní kontroly bez nových nálezů
  - Duplicitní informace (stejná informace z více záznamů)
  - Administrativní záznamy
  - Kontroly s výsledkem "bez změn" nebo "stabilní stav"
  - Opakované měření stejných hodnot bez významné změny

POSTUP:

1. Projdi všechny highlights chronologicky
2. Identifikuj klíčové milníky v průběhu onemocnění
3. Odstraň duplicity a rutinní kontroly
4. Zaměř se na události, které mění léčebný plán nebo prognózu
5. Preferuj NOVÉ informace před opakováním

PRAVIDLO DUPLICIT:

Pokud se stejná informace opakuje ve více záznamech (např. TNM klasifikace):
- Zachovej PRVNÍ výskyt (nejstarší datum)
- Zachovej další výskyty pouze pokud se hodnota ZMĚNILA

PRAVIDLO RUTINNÍCH KONTROL:

Pokud je série kontrol s konstantním stavem:
- Zachovej PRVNÍ kontrolu, která tento stav popisuje
- Odstranit opakující se kontroly se stejným zjištěním

CÍL:

Výsledný seznam by měl obsahovat 3-10 highlights pro typického pacienta.
Má poskytnout rychlý, výstižný přehled klíčových událostí v průběhu léčby.

VÝSTUP:

1. **selected_highlights**: Seznam indexů (0-based) highlights, které mají být zachovány
2. **reasoning**: Stručné vysvětlení (2-5 vět) logiky výběru

Příklad:
selected_highlights: [0, 2, 5, 8, 12]
reasoning: "Vybrány klíčové milníky: první diagnóza, TNM klasifikace, zjištění metastáz, změna léčby a významná komplikace. Odstraněny rutinní kontroly bez nových nálezů."
"""

    return prompt
