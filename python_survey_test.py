# -*- coding: utf-8 -*-
"""BWM Enquête — Volledige versie"""

import streamlit as st
import json
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ─────────────────────────────────────────────
# AFBEELDINGEN — pas deze namen aan naar uw PNG-bestanden
# Plaats alle afbeeldingen in de submap "images" naast dit script
# ─────────────────────────────────────────────
IMAGES = {
    "intro":        "factors_nl.drawio.png",       # Welkomstpagina — volledig overzicht
    "categories":   "categorieen.drawio.png",       # Categorie selectie + vergelijkingspagina's
    "category_1":   "dienstkenmerken.drawio.png",   # Dienstkenmerken
    "category_2":   "gebruikerservaring.drawio.png", # Gebruikerservaring
    "category_3":   "integratie.drawio.png",        # Integratie in stedelijke netwerken
    "category_4":   "bereikbaarheid.drawio.png",    # Bereikbaarheid van stations
    "category_5":   "ruimtelijke.drawio.png",       # Ruimtelijke ontwikkeling bij stations
}


st.set_page_config(page_title="BWM Enquête", layout="wide", page_icon="🚆")

st.markdown("""
<style>
    .block-container { max-width: 800px; margin: 0 auto; padding-top: 2rem; }

    /* ── Card-style buttons ── */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        font-weight: 400 !important;
        text-align: left !important;
        padding: 10px 16px !important;
        box-shadow: none !important;
        width: 100% !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: #1e293b !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: #eff6ff !important;
        border: 1.5px solid #3b82f6 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 10px 16px !important;
        box-shadow: none !important;
        width: 100% !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: #dbeafe !important;
        border-color: #2563eb !important;
        color: #1e293b !important;
    }

    /* ── Comparison label tooltips ── */
    .tip { display:inline-block; position:relative; cursor:help;
           margin-left:5px; vertical-align:middle; }
    .tip-icon {
        display:inline-flex; align-items:center; justify-content:center;
        width:17px; height:17px; border-radius:50%;
        background:#3b82f6; color:white;
        font-size:10px; font-weight:700; font-style:italic;
        font-family:Georgia,serif; line-height:1;
    }
    .tip-text {
        visibility:hidden; opacity:0;
        background:#1e293b; color:#f1f5f9;
        font-size:0.82rem; line-height:1.5; border-radius:6px;
        padding:9px 13px; position:absolute; z-index:9999;
        left:24px; top:-6px; width:320px;
        box-shadow:0 4px 16px rgba(0,0,0,0.22);
        transition:opacity 0.15s ease; pointer-events:none;
    }
    .tip:hover .tip-text { visibility:visible; opacity:1; }

    /* ── Comparison label ── */
    .bwm-cmp { font-size:0.97rem; margin-bottom:4px; color:#1e293b; }
    .bwm-cmp .ta { font-weight:600; }
    .bwm-cmp .tb { color:#64748b; }

    /* ── Wide sidebar ── */
    section[data-testid="stSidebar"] {
        width: 420px !important;
        min-width: 420px !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 420px !important;
    }

    /* ── Image placeholder ── */
    .img-placeholder {
        width:100%; height:180px;
        background:#f1f5f9;
        border:2px dashed #cbd5e1;
        border-radius:8px;
        display:flex; align-items:center; justify-content:center;
        color:#94a3b8; font-size:0.9rem;
        margin-bottom:1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
category_descriptions = {
    "Dienstkenmerken":
        "Factoren die betrekking hebben op de operationele prestaties en het serviceniveau van het vervoerssysteem.",
    "Gebruikerservaring":
        "Factoren die betrekking hebben op de kwaliteit, eenvoud en aantrekkelijkheid van de reiservaring voor gebruikers.",
    "Integratie in stedelijke netwerken":
        "Factoren die betrekking hebben op de mate waarin het systeem ruimtelijk, operationeel en functioneel is geïntegreerd met stedelijke vervoersnetwerken.",
    "Bereikbaarheid van stations":
        "Factoren die betrekking hebben op de toegankelijkheid van stations en de eenvoud waarmee reizigers het netwerk kunnen bereiken.",
    "Ruimtelijke ontwikkeling bij stations":
        "Factoren die betrekking hebben op de ruimtelijke structuur en ontwikkeling rondom stations en corridors.",
}

factor_descriptions = {
    "Dienstkenmerken": {
        "Bedieningsperiode":
            "De mate waarin de dienst beschikbaar is gedurende de dag en week, zoals laat in de avond en weekenden.",
        "Betrouwbaarheid":
            "De mate waarin reistijden en diensten punctueel, consistent en voorspelbaar zijn.",
        "Dienstfrequentie":
            "De mate waarin hoge en regelmatige frequenties worden aangeboden.",
        "Reistijd":
            "De mate waarin het systeem korte reistijden mogelijk maakt, onder andere door korte halteertijden.",
        "Tariefniveau":
            "De mate waarin tarieven concurrerend en betaalbaar zijn.",
    },
    "Gebruikerservaring": {
        "Comfort":
            "De mate waarin een comfortabele en aangename reiservaring wordt geboden, inclusief capaciteit, netheid en sociale veiligheid.",
        "Reisinformatie":
            "De mate waarin duidelijke en actuele reisinformatie beschikbaar is online en op stations, en waarin navigeren op stations eenvoudig is.",
        "Systeemidentiteit":
            "De mate waarin voertuigen en stations een duidelijke, herkenbare en aantrekkelijke identiteit hebben die het onderscheidt van andere OV-diensten.",
    },
    "Integratie in stedelijke netwerken": {
        "Doorkoppeling in stedelijke gebieden":
            "De mate waarin diensten door stedelijke gebieden worden doorgekoppeld en meerdere stedelijke corridors direct verbinden zonder overstappen.",
        "Overstapintegratie met BTM":
            "De mate waarin dienstregelingen en fysieke overstappen op BTM op elkaar zijn afgestemd om soepele multimodale reizen mogelijk te maken.",
        "Tarief- en ticketintegratie met BTM":
            "De mate waarin tarieven en ticketsystemen zijn geïntegreerd over modaliteiten en vervoerders, zodat drempelloos reizen mogelijk is.",
    },
    "Bereikbaarheid van stations": {
        "Loop- en fietsbereikbaarheid van stations":
            "De mate waarin stations goed bereikbaar zijn te voet en per fiets, inclusief de beschikbaarheid van voldoende stallingen.",
        "Parkeervoorzieningen bij stations (P+R)":
            "De mate waarin bepaalde stations parkeervoorzieningen bieden om de overstap van auto naar trein te faciliteren.",
        "Stationsdichtheid":
            "De mate waarin stations voldoende dicht en ruimtelijk evenwichtig zijn verspreid om brede toegang tot het netwerk te bieden.",
    },
    "Ruimtelijke ontwikkeling bij stations": {
        "Coördinatie ruimte en mobiliteit":
            "De mate waarin ruimtelijke ontwikkeling en het vervoerssysteem op elkaar zijn afgestemd in locatie, functie en ontwikkeling.",
        "Dichtheid rond stations":
            "De mate waarin bevolking en activiteiten geconcentreerd zijn in de omgeving van stations.",
        "Functiemix rond stations":
            "De mate waarin verschillende functies (zoals wonen, werken, onderwijs en voorzieningen) aanwezig zijn in stationsgebieden om verschillende reismotieven te ondersteunen.",
    },
}

categories = {cat: list(f.keys()) for cat, f in factor_descriptions.items()}

# ─────────────────────────────────────────────
# BWM 1–9 schaal
# Alleen ankerpunten hebben labels
# ─────────────────────────────────────────────

scale_labels = {
    1: "Even belangrijk",
    3: "Licht belangrijker",
    5: "Duidelijk belangrijker",
    7: "Veel belangrijker",
    9: "Extreem belangrijker",
}

# ─────────────────────────────────────────────
# STEP DEFINITIONS
# New order: select best+worst together, then bto, then otw
# ─────────────────────────────────────────────
cat_list = list(categories.keys())
N = len(cat_list)
STEP_INTRO            = 1
STEP_CONSENT          = 2        # GDPR consent page
STEP_PERSONAL         = 3
STEP_CAT_SELECT       = 4        # best+worst category (separate page)
STEP_CAT_CMP          = 5        # category bto+otw comparisons (separate page)
# Per category: 2 pages each
# STEP_FACTOR_SEL_START + 2*i   = select best+worst for category i
# STEP_FACTOR_SEL_START + 2*i+1 = bto+otw comparisons for category i
STEP_FACTOR_SEL_START = 6
STEP_SUMMARY          = 6 + 2 * N
STEP_THANKYOU         = 6 + 2 * N + 1
TOTAL_STEPS           = STEP_SUMMARY  # progress bar goes up to summary only

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for _k, _v in [("step", STEP_INTRO), ("data", {}), ("errors", []),
               ("do_scroll", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Generate unique respondent ID and record start time on first load
if "respondent_id" not in st.session_state:
    import string
    _chars = string.ascii_uppercase + string.digits
    st.session_state.respondent_id = (
        ''.join(random.choices(_chars, k=3)) + '-' +
        ''.join(random.choices(_chars, k=3))
    )
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.now()

# ─────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────
def save_progress():
    pass  # Data lives in st.session_state for the duration of the session

def clear_progress():
    pass

# ─────────────────────────────────────────────
# GOOGLE SHEETS EXPORT
# ─────────────────────────────────────────────
def save_to_sheets(data: dict):
    """
    Saves survey response as a new row in Google Sheets.
    Credentials are loaded from st.secrets["gcp_service_account"].
    The sheet is identified by st.secrets["sheet_url"].

    To set up:
    1. Add your service account JSON to Streamlit secrets as [gcp_service_account]
    2. Add your sheet URL to secrets as sheet_url = "https://docs.google.com/..."
    3. Share the sheet with the service account email address
    """
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet  = client.open_by_url(st.secrets["sheet_url"]).sheet1

        # Build flat row from nested data
        p    = data.get("persoonlijk", {})
        bto  = data.get("categorie_best_to_others", {})
        otw  = data.get("categorie_others_to_worst", {})
        fac  = data.get("factoren", {})

        submit_time = datetime.now()
        start_time  = st.session_state.get("start_time", submit_time)
        duration_min = round((submit_time - start_time).total_seconds() / 60, 1)

        row = [
            st.session_state.get("respondent_id", ""),
            submit_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration_min,
            p.get("naam", ""),
            p.get("titel", ""),
            p.get("organisatie", ""),
            p.get("rol", ""),
            p.get("expertise", ""),
            p.get("opleiding", ""),
            p.get("ervaring", ""),
            data.get("categorie_best", ""),
            data.get("categorie_worst", ""),
            data.get("opmerkingen", ""),
        ]

        def to_num(value):
            """Values are already numeric."""
            return value if value else ""

        # Category bto values (numeric)
        for cat in cat_list:
            row.append(to_num(bto.get(cat, "")))

        # Category otw values (numeric)
        for cat in cat_list:
            row.append(to_num(otw.get(cat, "")))

        # Factor best, worst, bto, otw per category
        for cat in cat_list:
            cd = fac.get(cat, {})
            row.append(cd.get("best", ""))
            row.append(cd.get("worst", ""))
            for f in categories[cat]:
                row.append(to_num(cd.get("best_to_others", {}).get(f, "")))
            for f in categories[cat]:
                row.append(to_num(cd.get("others_to_worst", {}).get(f, "")))

        # Write header row if sheet is empty
        # Get all non-empty rows to reliably detect if header exists
        all_rows = sheet.get_all_values()
        non_empty = [r for r in all_rows if any(c.strip() for c in r)]
        if not non_empty:
            header = [
                "Respondent ID", "Timestamp", "Duur (min)",
                "Naam", "Titel", "Organisatie", "Rol",
                "Expertise", "Opleiding", "Ervaring",
                "Categorie Best", "Categorie Worst", "Opmerkingen",
            ]
            for cat in cat_list:
                header.append(f"BTO: {cat}")
            for cat in cat_list:
                header.append(f"OTW: {cat}")
            for cat in cat_list:
                header += [f"{cat} Best", f"{cat} Worst"]
                for f in categories[cat]:
                    header.append(f"{cat} BTO: {f}")
                for f in categories[cat]:
                    header.append(f"{cat} OTW: {f}")
            sheet.append_row(header, value_input_option="RAW")

        sheet.append_row(row, value_input_option="RAW")
        return True

    except Exception as e:
        return False

# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────
def next_step():
    st.session_state.step += 1
    st.session_state.errors = []
    st.session_state.do_scroll = True

def prev_step():
    st.session_state.step -= 1
    st.session_state.errors = []
    st.session_state.do_scroll = True

def show_errors():
    for e in st.session_state.errors:
        st.error(e)

def nav_buttons(can_proceed=True):
    col1, col2 = st.columns(2)
    if st.session_state.step > STEP_INTRO:
        col1.button("← Vorige", on_click=prev_step)
    col2.button("Volgende →", on_click=next_step,
                disabled=not can_proceed, type="primary")
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def tip_html(desc):
    d = desc.replace("'","&#39;").replace('"',"&quot;")
    return (
        '<span class="tip"><span class="tip-icon">i</span>'
        '<span class="tip-text">' + d + '</span></span>'
    )

def card_select(options, state_key, descriptions=None):
    """
    Card-style selector. None = nothing selected (all white).
    Returns selected value or None if nothing chosen yet.
    """
    descriptions = descriptions or {}

    # Default to None (nothing selected) unless already set to a valid option
    if state_key not in st.session_state or st.session_state[state_key] not in options:
        # Try to restore from saved data
        if state_key == "best_cat_sel":
            saved = st.session_state.data.get("categorie_best", None)
        elif state_key == "worst_cat_sel":
            saved = st.session_state.data.get("categorie_worst", None)
        else:
            # Factor keys are pre-seeded before card_select is called
            saved = st.session_state.get(state_key, None)
        st.session_state[state_key] = saved if saved in options else None

    current = st.session_state[state_key]

    for opt in options:
        selected = (opt == current)

        def _make_setter(v):
            def _set(): st.session_state[state_key] = v
            return _set

        st.button(opt, key=f"_card_{state_key}_{opt}",
                  on_click=_make_setter(opt),
                  use_container_width=True,
                  type="primary" if selected else "secondary")

    if current and descriptions.get(current):
        st.markdown(
            f'<div style="background:#f0f9ff;border-left:3px solid #3b82f6;'
            f'border-radius:4px;padding:8px 12px;margin-top:4px;'
            f'font-size:0.85rem;color:#1e3a5f;line-height:1.5;">'
            f'<strong>{current}:</strong> {descriptions[current]}</div>',
            unsafe_allow_html=True)
    st.markdown("")
    return current

def scale_slider(label, key, saved_value=None):

    options = list(range(1, 10))

    default = saved_value if saved_value in options else 1

    chosen = st.select_slider(
        label,
        options=options,
        value=default,
        format_func=lambda x: (
            f"{x} — {scale_labels[x]}"
            if x in scale_labels
            else str(x)
        ),
        key=key
    )

    if chosen in scale_labels:
        st.caption(f"Interpretatie: **{scale_labels[chosen]}**")
    else:
        st.caption("Tussenliggende waarde")

    return chosen

def compare_label(term_a, desc_a, term_b, desc_b):
    tip_a = tip_html(desc_a) if desc_a else ""
    tip_b = tip_html(desc_b) if desc_b else ""
    st.markdown(
        '<p class="bwm-cmp">Hoe veel belangrijker is '
        '<span class="ta">' + term_a + '</span>' + tip_a +
        ' dan <span class="tb">' + term_b + '</span>' + tip_b + '?</p>',
        unsafe_allow_html=True)

def _img_b64(key: str) -> str:
    """Return base64 data URI for an image key, or empty string if not found."""
    from pathlib import Path
    import base64
    filename = IMAGES.get(key, "")
    if not filename:
        return ""
    path = Path(__file__).parent / "images_nl" / filename
    if not path.exists():
        return ""
    with open(str(path), "rb") as fh:
        return base64.b64encode(fh.read()).decode()

def _float_image_html(key: str, width: int = 280) -> str:
    """Return HTML for a float:right image."""
    b64 = _img_b64(key)
    if not b64:
        return ""
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'width="{width}" '
        f'style="float:right;margin-left:24px;margin-bottom:12px;">' 
    )


def show_page_image(key: str, width: int = None):
    """
    Display a PNG from the IMAGES dict. Images live in the 'images' subfolder.
    width: optional pixel width to constrain the image (e.g. 300 for smaller).
    """
    from pathlib import Path
    filename = IMAGES.get(key, "")
    if not filename:
        return
    path = Path(__file__).parent / "images_nl" / filename
    if path.exists():
        if width:
            # Wrap in a div with left margin to nudge image right
            import base64
            with open(str(path), "rb") as img_file:
                b64 = base64.b64encode(img_file.read()).decode()
            st.markdown(
                f'<div style="margin-left:20px;">' +
                f'<img src="data:image/png;base64,{b64}" width="{width}" style="max-width:100%;">' +
                f'</div>',
                unsafe_allow_html=True)
        else:
            st.image(str(path), use_container_width=True)
    else:
        st.markdown(
            f'<div class="img-placeholder">📷 Afbeelding niet gevonden: images/{filename}</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# SIDEBAR — volledig overzicht op elke pagina

# ─────────────────────────────────────────────
# SCROLL TO TOP
# ─────────────────────────────────────────────
if st.session_state.do_scroll:
    _tok = random.randint(0, 9999999)
    st.components.v1.html(f"""<script>
// {_tok}
(function() {{
    function doScroll() {{
        try {{
            var d = window.parent.document;
            ['section.main','[data-testid="stMain"]',
             '[data-testid="stAppViewContainer"] > section'].forEach(function(s) {{
                var el = d.querySelector(s);
                if (el) el.scrollTop = 0;
            }});
            d.documentElement.scrollTop = 0;
            d.body.scrollTop = 0;
            window.parent.scrollTo(0,0);
        }} catch(e) {{}}
    }}
    doScroll();
    setTimeout(doScroll, 120);
    setTimeout(doScroll, 350);
}})();
</script>""", height=0)
    st.session_state.do_scroll = False

# ─────────────────────────────────────────────
# SIDEBAR — volledig overzicht op elke pagina
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Volledig overzicht")
    st.caption("Categorieën (Niveau 1) en factoren (Niveau 2)")
    show_page_image("intro")

# ─────────────────────────────────────────────
# PROGRESS BAR
# ─────────────────────────────────────────────
if st.session_state.step < STEP_THANKYOU:
    pct = min((st.session_state.step - 1) / max(TOTAL_STEPS - 1, 1), 1.0)
    st.progress(pct)
    st.caption(f"Voortgang: **{int(pct * 100)}%** voltooid")
    st.markdown("---")


# ══════════════════════════════════════════════
# STEP 1: INTRODUCTIE
# ══════════════════════════════════════════════
if st.session_state.step == STEP_INTRO:
    st.title("🚆 Succesfactoren voor Voorstedelijk Spoorvervoer")
    st.subheader("Expertenquête — Best-Worst Methode (BWM)")
    st.markdown("""
**Welkom bij deze expertenquête.** Dit onderzoek richt zich op het identificeren van
factoren die bijdragen aan het potentiële vraagstucces van voorstedelijk spoorvervoer
in de Nederlandse context. De uitkomsten bieden een raamwerk voor besluitvorming over
de implementatie van dergelijke diensten in Nederland, en worden gebruikt als invoer
voor een modelleringsstudie.

### Werkwijze
Het onderzoek is opgebouwd in twee niveaus:

- **Niveau 1 — Categorieën:** Eerst worden de vijf hoofdcategorieën ten opzichte van
  elkaar gerangschikt.
- **Niveau 2 — Factoren:** Vervolgens worden per categorie de factoren ten opzichte van
  elkaar gerangschikt.

Per niveau wordt u gevraagd:
1. De **meest belangrijke** en **minst belangrijke** factor of categorie aan te wijzen
2. **Best-to-others**: hoeveel belangrijker is de beste dan alle anderen?
3. **Others-to-worst**: hoeveel belangrijker is elke andere dan de slechtste?

### Categorieën & factoren
""")
    for cat, factors in categories.items():
        st.markdown(f"- **{cat}**: {', '.join(factors)}")
    st.info("💡 Het volledige overzicht van categorieën en factoren is te vinden in de **zijbalk** links ←")
    st.button("Start enquête →", on_click=next_step, type="primary")

# ══════════════════════════════════════════════
# STEP 2: TOESTEMMING (GDPR CONSENT)
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_CONSENT:
    st.title("📋 Toestemming & Privacy")
    st.markdown("""
### Informatie over dit onderzoek

Dit onderzoek wordt uitgevoerd door **Luuk Spijker** als onderdeel van een afstudeeronderzoek
aan de **Universiteit Twente** (faculteit ITC / Civiele Techniek).

Het doel is het bepalen van de relatieve belangrijkheid van succesfactoren voor voorstedelijk
spoorvervoer met behulp van de Best-Worst Methode (BWM).
""")

    st.markdown("---")
    st.subheader("🔒 Hoe gaan wij om met uw gegevens?")
    st.markdown("""
- **Wat wordt verzameld:** uw rol, organisatie, expertisegebied en de antwoorden op de vergelijkingsvragen.
  Uw naam is **optioneel** en niet vereist voor deelname.
- **Opslag:** alle gegevens worden opgeslagen in een beveiligd Google Workspace-account
  gekoppeld aan de Universiteit Twente (@utwente.nl).
- **Toegang:** alleen de onderzoeker (Luuk Spijker) en de begeleidende supervisor hebben
  toegang tot de ruwe data.
- **Bewaartermijn:** alle verzamelde data wordt verwijderd na afronding en goedkeuring
  van het onderzoek (uiterlijk december 2025).
- **Rechtsgrond:** deelname is vrijwillig en gebaseerd op uw toestemming (AVG Art. 6(1)(a)).
- **Recht op intrekking:** u kunt uw deelname te allen tijde intrekken en verzoeken om
  verwijdering van uw data door contact op te nemen via
  **l.spijker@student.utwente.nl**.
- **Privacyverklaring:** zie de [privacyverklaring van de Universiteit Twente](https://www.utwente.nl/en/privacy/).
""")

    st.markdown("---")
    st.subheader("✅ Toestemming")
    st.markdown("Vink de onderstaande verklaring aan om door te gaan met de enquête.")

    c1 = st.checkbox(
        "Ik heb de bovenstaande informatie gelezen en begrepen, en ik geef toestemming "
        "voor de verwerking van mijn antwoorden ten behoeve van dit onderzoek.")
    c2 = st.checkbox(
        "Ik begrijp dat mijn deelname vrijwillig is en dat ik mijn toestemming te allen "
        "tijde kan intrekken door contact op te nemen met de onderzoeker.")

    all_consent = c1 and c2

    if not all_consent:
        st.info("Vink beide vakjes aan om door te gaan.")

    col1, col2 = st.columns(2)
    col1.button("← Vorige", on_click=prev_step)
    col2.button("Volgende →", on_click=next_step,
                disabled=not all_consent, type="primary")

# ══════════════════════════════════════════════
# STEP 3: PERSOONLIJKE GEGEVENS
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_PERSONAL:
    st.title("Persoonlijke informatie")
    st.markdown("Velden gemarkeerd met * zijn verplicht. Uw naam is optioneel.")
    p = st.session_state.data.get("persoonlijk", {})
    naam        = st.text_input("Volledige naam (optioneel)", value=p.get("naam",""))
    titel       = st.text_input("Titel(s)",              value=p.get("titel",""))
    organisatie = st.text_input("Organisatie *",         value=p.get("organisatie",""))
    expertise   = st.text_input("Expertise / vakgebied", value=p.get("expertise",""))
    rol_opts = ["-- Selecteer --","Onderzoeker","Beleidsmaker","Consultant","Vervoerder","Overheid","Anders"]
    rol = st.selectbox("Rol *", rol_opts,
        index=rol_opts.index(p.get("rol","-- Selecteer --")) if p.get("rol") in rol_opts else 0)
    opl_opts = ["-- Selecteer --","Bachelor","Master","PhD","Anders"]
    opleiding = st.selectbox("Hoogst behaalde opleiding", opl_opts,
        index=opl_opts.index(p.get("opleiding","-- Selecteer --")) if p.get("opleiding") in opl_opts else 0)
    erv_opts = ["-- Selecteer --","0-2 jaar","3-5 jaar","6-10 jaar","10+ jaar"]
    ervaring = st.selectbox("Aantal jaar relevante ervaring", erv_opts,
        index=erv_opts.index(p.get("ervaring","-- Selecteer --")) if p.get("ervaring") in erv_opts else 0)
    def clean(v, placeholder="-- Selecteer --"):
        return "" if v == placeholder else v
    st.session_state.data["persoonlijk"] = {
        "naam":naam,"titel":titel,"organisatie":organisatie,
        "rol":clean(rol),"expertise":expertise,
        "opleiding":clean(opleiding),"ervaring":clean(ervaring)}
    errors = []
    if not organisatie.strip():  errors.append("⚠️ Organisatie is verplicht.")
    if rol == "-- Selecteer --": errors.append("⚠️ Selecteer een rol.")
    show_errors()
    save_progress()
    nav_buttons(can_proceed=len(errors)==0)

# ══════════════════════════════════════════════
# STEP 3: BESTE CATEGORIE + BEST-TO-OTHERS
# ══════════════════════════════════════════════
# ══════════════════════════════════════════════
# STEP 3: SELECTEER BESTE + SLECHTSTE CATEGORIE
# ══════════════════════════════════════════════
# ══════════════════════════════════════════════
# STEP 3: CATEGORIEVERGELIJKING (alles op één pagina)
# ══════════════════════════════════════════════
# ══════════════════════════════════════════════
# STEP 3: SELECTEER BESTE + SLECHTSTE CATEGORIE
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_CAT_SELECT:
    st.title("Categorievergelijking — Stap 1 van 2")
    st.markdown("Selecteer de categorie die u **het meest** en **het minst belangrijk** vindt.")

    if "best_cat_sel" not in st.session_state:
        saved_bc = st.session_state.data.get("categorie_best", None)
        st.session_state["best_cat_sel"] = saved_bc if saved_bc in cat_list else None

    st.markdown("**⭐ Meest belangrijke categorie**")
    st.caption("_💡 Klik op een optie om de omschrijving te bekijken._")
    best_cat = card_select(cat_list, "best_cat_sel", descriptions=category_descriptions)
    if best_cat:
        st.session_state.data["categorie_best"] = best_cat

    st.markdown("---")
    remaining = [c for c in cat_list if c != best_cat] if best_cat else cat_list
    if "worst_cat_sel" not in st.session_state:
        saved_wc = st.session_state.data.get("categorie_worst", None)
        st.session_state["worst_cat_sel"] = saved_wc if saved_wc in remaining else None
    if st.session_state.get("worst_cat_sel") not in remaining:
        st.session_state["worst_cat_sel"] = None

    st.markdown("**⚪ Minst belangrijke categorie**")
    st.caption("_💡 Klik op een optie om de omschrijving te bekijken._")
    worst_cat = card_select(remaining, "worst_cat_sel", descriptions=category_descriptions)
    if worst_cat:
        st.session_state.data["categorie_worst"] = worst_cat

    errors = []
    if not best_cat:
        errors.append("⚠️ Selecteer de meest belangrijke categorie.")
    if not worst_cat:
        errors.append("⚠️ Selecteer de minst belangrijke categorie.")
    if best_cat and worst_cat and worst_cat == best_cat:
        errors.append("⚠️ De minst belangrijke categorie mag niet gelijk zijn aan de meest belangrijke.")
    save_progress()
    show_errors()
    nav_buttons(can_proceed=len(errors) == 0)

# ══════════════════════════════════════════════
# STEP 4: CATEGORIE VERGELIJKINGEN (bto + otw)
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_CAT_CMP:
    best_cat  = st.session_state.data.get("categorie_best", cat_list[0])
    worst_cat = st.session_state.data.get("categorie_worst", cat_list[-1])
    st.title("Categorievergelijking — Stap 2 van 2")


    st.subheader(f"Hoe veel belangrijker is '{best_cat}' dan de andere categorieën?")
    bto = st.session_state.data.get("categorie_best_to_others", {})
    for c in [x for x in cat_list if x != best_cat]:
        compare_label(best_cat, category_descriptions.get(best_cat, ""),
                      c,        category_descriptions.get(c, ""))
        bto[c] = scale_slider("", key=f"bto_cat_{c}", saved_value=bto.get(c))
        st.markdown("")
    st.session_state.data["categorie_best_to_others"] = bto

    st.markdown("---")
    st.subheader(f"Hoe veel belangrijker zijn de andere categorieën dan '{worst_cat}'?")
    otw = st.session_state.data.get("categorie_others_to_worst", {})
    for c in [x for x in cat_list if x != worst_cat]:
        compare_label(c,         category_descriptions.get(c, ""),
                      worst_cat, category_descriptions.get(worst_cat, ""))
        otw[c] = scale_slider("", key=f"otw_cat_{c}", saved_value=otw.get(c))
        st.markdown("")
    st.session_state.data["categorie_others_to_worst"] = otw
    save_progress()
    nav_buttons()

# ══════════════════════════════════════════════
# STEPS 5..5+2N-1: PER CATEGORIE 2 PAGINA'S
#   even offset (0,2,4,...) = selecteer beste+slechtste factor
#   odd  offset (1,3,5,...) = bto+otw vergelijkingen
# ══════════════════════════════════════════════
elif STEP_FACTOR_SEL_START <= st.session_state.step < STEP_SUMMARY:
    offset    = st.session_state.step - STEP_FACTOR_SEL_START
    cat_index = offset // 2
    page_type = offset % 2   # 0 = selectie, 1 = vergelijkingen
    cat       = cat_list[cat_index]
    factors   = categories[cat]

    if "factoren" not in st.session_state.data:
        st.session_state.data["factoren"] = {}
    if cat not in st.session_state.data["factoren"]:
        st.session_state.data["factoren"][cat] = {}

    if page_type == 0:
        # ── Pagina A: selecteer beste + slechtste factor ──
        st.title(f"Categorie {cat_index + 1} van {N}: {cat}")
        show_page_image(f"category_{cat_index + 1}")
        st.markdown(f"Selecteer de **meest** en **minst belangrijke** factor binnen **{cat}**.")

        sel_key_b = f"best_f_sel_{cat}"
        if sel_key_b not in st.session_state:
            saved_b = st.session_state.data["factoren"][cat].get("best", None)
            st.session_state[sel_key_b] = saved_b if saved_b in factors else None

        st.markdown("**⭐ Meest belangrijke factor**")
        st.caption("_💡 Klik op een optie om de omschrijving te bekijken._")
        best_f = card_select(factors, sel_key_b, descriptions=factor_descriptions.get(cat, {}))
        st.session_state.data["factoren"][cat]["best"] = best_f

        st.markdown("---")
        remaining_f = [f for f in factors if f != best_f]
        sel_key_w = f"worst_f_sel_{cat}"
        if sel_key_w not in st.session_state:
            saved_w = st.session_state.data["factoren"][cat].get("worst", None)
            st.session_state[sel_key_w] = saved_w if saved_w in remaining_f else None

        st.markdown("**⚪ Minst belangrijke factor**")
        st.caption("_💡 Klik op een optie om de omschrijving te bekijken._")
        worst_f = card_select(remaining_f, sel_key_w, descriptions=factor_descriptions.get(cat, {}))
        st.session_state.data["factoren"][cat]["worst"] = worst_f

        errors = []
        if best_f is None:
            errors.append("⚠️ Selecteer de meest belangrijke factor.")
        if worst_f is None:
            errors.append("⚠️ Selecteer de minst belangrijke factor.")
        if best_f and worst_f and worst_f == best_f:
            errors.append(f"⚠️ De minst belangrijke factor mag niet gelijk zijn aan de meest belangrijke ({best_f}).")
        show_errors()
        save_progress()
        nav_buttons(can_proceed=len(errors) == 0)

    else:
        # ── Pagina B: bto + otw vergelijkingen ──
        cat_data = st.session_state.data["factoren"][cat]
        best_f   = cat_data.get("best", factors[0])
        worst_f  = cat_data.get("worst", factors[-1])

        st.title(f"Categorie {cat_index + 1} van {N}: {cat} — Vergelijkingen")
        show_page_image(f"category_{cat_index + 1}")

        st.subheader(f"Hoe veel belangrijker is '{best_f}' dan de andere factoren?")
        bto_f = cat_data.get("best_to_others", {})
        for f in [x for x in factors if x != best_f]:
            compare_label(best_f, factor_descriptions.get(cat, {}).get(best_f, ""),
                          f,      factor_descriptions.get(cat, {}).get(f, ""))
            bto_f[f] = scale_slider("", key=f"bto_{cat}_{f}", saved_value=bto_f.get(f))
            st.markdown("")
        st.session_state.data["factoren"][cat]["best_to_others"] = bto_f

        st.markdown("---")
        st.subheader(f"Hoe veel belangrijker zijn de andere factoren dan '{worst_f}'?")
        otw_f = cat_data.get("others_to_worst", {})
        for f in [x for x in factors if x != worst_f]:
            compare_label(f,       factor_descriptions.get(cat, {}).get(f, ""),
                          worst_f, factor_descriptions.get(cat, {}).get(worst_f, ""))
            otw_f[f] = scale_slider("", key=f"otw_{cat}_{f}", saved_value=otw_f.get(f))
            st.markdown("")
        st.session_state.data["factoren"][cat]["others_to_worst"] = otw_f
        save_progress()
        nav_buttons()

# ══════════════════════════════════════════════
# FINAL: OVERZICHT & VERZENDEN
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_SUMMARY:
    st.title("✅ Overzicht & Verzenden")
    st.markdown("Controleer uw antwoorden hieronder. U kunt teruggaan om aanpassingen te maken.")

    with st.expander("👤 Persoonlijke gegevens", expanded=False):
        for k, v in st.session_state.data.get("persoonlijk", {}).items():
            st.write(f"**{k.capitalize()}**: {v}")

    with st.expander("📊 Categorievergelijkingen", expanded=True):
        bc = st.session_state.data.get("categorie_best", "—")
        wc = st.session_state.data.get("categorie_worst", "—")
        st.write(f"**Meest belangrijk**: {bc} | **Minst belangrijk**: {wc}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Best-to-others:**")
            for k, v in st.session_state.data.get("categorie_best_to_others", {}).items():
                st.write(f"- {k}: {v}")
        with col2:
            st.markdown("**Others-to-worst:**")
            for k, v in st.session_state.data.get("categorie_others_to_worst", {}).items():
                st.write(f"- {k}: {v}")

    for cat in cat_list:
        cd = st.session_state.data.get("factoren", {}).get(cat, {})
        with st.expander(f"🔍 {cat}", expanded=False):
            st.write(f"**Meest belangrijk**: {cd.get('best','—')} | **Minst belangrijk**: {cd.get('worst','—')}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Best-to-others:**")
                for k, v in cd.get("best_to_others", {}).items():
                    st.write(f"- {k}: {v}")
            with col2:
                st.markdown("**Others-to-worst:**")
                for k, v in cd.get("others_to_worst", {}).items():
                    st.write(f"- {k}: {v}")

    st.markdown("---")
    st.subheader("💬 Opmerkingen & aanbevelingen")
    st.markdown("Heeft u nog opmerkingen, vragen of aanbevelingen met betrekking tot dit onderzoek?")
    opmerkingen = st.text_area(
        "Uw opmerkingen (optioneel)",
        value=st.session_state.data.get("opmerkingen", ""),
        height=120,
        placeholder="Typ hier eventuele opmerkingen..."
    )
    st.session_state.data["opmerkingen"] = opmerkingen

    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.button("← Vorige", on_click=prev_step)
    already_submitted = st.session_state.get("submitted", False)
    if already_submitted:
        st.success("✅ Uw antwoorden zijn al verzonden. U kunt dit tabblad sluiten.")
    elif col2.button("📨 Verzend enquête", type="primary"):
        with st.spinner("Antwoorden opslaan..."):
            success = save_to_sheets(st.session_state.data)
        if success:
            st.session_state.submitted = True
            clear_progress()
            st.session_state.step = STEP_THANKYOU
            st.rerun()
        else:
            st.error("❌ Er is iets misgegaan. Probeer opnieuw of neem contact op via l.spijker@student.utwente.nl")
            with st.expander("📋 Ruwe data (backup — kopieer dit indien nodig)", expanded=True):
                st.json(st.session_state.data)

# ══════════════════════════════════════════════
# THANK-YOU PAGE
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_THANKYOU:
    st.balloons()
    st.markdown("""
<div style="text-align:center;padding:3rem 1rem;">
  <div style="font-size:4rem;margin-bottom:1rem;">🎉</div>
  <h1 style="color:#1e293b;">Hartelijk bedankt voor uw deelname!</h1>
  <p style="font-size:1.1rem;color:#475569;max-width:500px;margin:1rem auto 2rem;">
    Uw antwoorden zijn succesvol opgeslagen en dragen bij aan het onderzoek naar
    succesfactoren voor voorstedelijk spoorvervoer.
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:2rem 0;">
  <p style="color:#64748b;font-size:0.95rem;">
    Heeft u vragen over het onderzoek? Neem dan contact op via:<br>
    <strong>📧 <a href="mailto:l.spijker@student.utwente.nl" style="color:#3b82f6;">
    l.spijker@student.utwente.nl</a></strong>
  </p>
  <p style="color:#94a3b8;font-size:0.9rem;margin-top:2rem;">
    U kunt dit tabblad nu sluiten.
  </p>
</div>
""", unsafe_allow_html=True)
