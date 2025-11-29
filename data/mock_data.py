mock_questions = [
    (
        1,
        "Datum stanovení diagnózy",
        """
   - Datum, kdy byla poprvé stanovena diagnóza karcinomu prsu
   - Může být přímé ("5. října 2022") nebo odvozené z kontextu
   - Relevantní text může obsahovat taky pouze informaci o stanovení diagnózy bez přesného data, ten se vyplní deterministicky z data dokumentu.""",
    ),
    (
        2,
        "Klinická TNM klasifikace",
        """
   - Klinická klasifikace: cTNM (např. "cT2N0M0")
   - Stanovuje se před zahájením léčby na základě klinického vyšetření a zobrazovacích metod.
   - Extrahuj všechny výskyty, i když se opakují"""
    ),
    (
        3,
        "Patologická TNM klasifikace",
        """
   - Patologická klasifikace: pTNM (např. "pT2 pN0(i−)(sn) M0")
   - Stanovuje se po chirurgickém odstranění tumoru na základě histologického vyšetření.
   - Extrahuj všechny výskyty, i když se opakují"""
    ),
    (
        4,
        "ER (estrogenové receptory)",
        """
   - Status estrogenových receptorů
   - Hodnoty mohou být v procentech (např. "ER 90%"), pozitivní/negativní, nebo pomocí skóre."""
    ),
    (
        5,
        "PR (progesteronové receptory)",
        """
   - Status progesteronových receptorů
   - Hodnoty mohou být v procentech (např. "PR 5%"), pozitivní/negativní, nebo pomocí skóre."""
    ),
    (
        6,
        "HER2 status",
        """
   - Status receptoru HER2 (Human Epidermal growth factor Receptor 2)
   - Hodnoty jako "0", "1+", "2+", "3+", "negativní", "pozitivní", nebo výsledek testování (FISH, SISH)."""
    ),
    (
        7,
        "Ki-67 (proliferační index)",
        """
   - Proliferační aktivita nádoru
   - Hodnoty jsou obvykle v procentech (např. "Ki-67 20%")."""
    ),
    (
        8,
        "Léčba mimo MOÚ",
        """
   - Zmínky o léčbě v jiné nemocnici nebo zdravotnickém zařízení
   - Je důležité vědět, jestli pacient absolvoval léčbu mimo MOÚ, hlavně před první návštěvou v MOÚ, případně mezi cykly systémové léčby.
   - Může jít o ambulance, regionální nemocnice, domácí péče mimo MOÚ"""
    ),
    (
        9,
        "Progrese, recidiva nebo metastázy",
        """
   - Informace o zhoršení onemocnění, jeho návratu nebo rozšíření
   - Progrese: Růst tumoru, nová ložiska, zhoršení stavu
   - Recidiva: Lokální nebo vzdálený návrat onemocnění po léčbě
   - Vzdálené metastázy: Výskyt metastáz v orgánech jako játra, kosti, plíce, mozek, atd."""
    )
]