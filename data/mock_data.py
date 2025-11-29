mock_questions = [
    (
        1,
        "Datum stanovení diagnózy",
        """
   - Datum, kdy byla poprvé stanovena diagnóza karcinomu prsu
   - Může být přímé ("5. října 2022") nebo odvozené z kontextu
   - Označ jako `inferred: true` pokud datum odvozuješ"""
    ),
    (
        2,
        "TNM klasifikace",
        """
   - Klinická klasifikace: cTNM (např. "cT2N0M0")
   - Patologická klasifikace: pTNM (např. "pT2 pN0(i−)(sn) M0")
   - Extrahuj všechny výskyty, i když se opakují"""
    ),
    (
        3,
        "Hormonální receptory",
        """
   - ER (estrogenové receptory): hodnoty v % nebo pozitivní/negativní
   - PR (progesteronové receptory): hodnoty v % nebo pozitivní/negativní
   - HER2: hodnoty jako "0", "negativní", "pozitivní"""
    ),
    (4,
        "Léčba mimo MOÚ",
        """
   - Zmínky o léčbě v jiné nemocnici nebo zdravotnickém zařízení
   - Je důležité vědět, jestli pacient absolvoval léčbu mimo MOÚ, hlavně před první návštěvou v MOÚ, případně mezi cykly systémové léčby.
   - Může jít o ambulance, regionální nemocnice, domácí péče mimo MOÚ"""
    ),
    (5,
        "Progrese",
        """
   - Informace o progresi/zhoršení onemocnění
   - Růst tumoru, nová ložiska, zhoršení stavu"""
    ),
    (6,
        "Recidiva",
        """
   - Zmínky o recidivě nebo návratu onemocnění
   - Lokální i vzdálená recidiva"""
    ),
    (7,
        "Vzdálené metastázy",
        """
   - Výskyt metastáz v různých lokacích
   - Játra, kosti, plíce, mozek, atd."""
    )
]
