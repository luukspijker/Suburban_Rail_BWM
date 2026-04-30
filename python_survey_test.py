# -*- coding: utf-8 -*-
"""BWM Enquête — Volledige versie"""

import streamlit as st
import json
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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
    "Service- en systeemkenmerken":
        "De operationele prestaties van het spoorsysteem zoals frequentie, snelheid, beschikbaarheid en betrouwbaarheid.",
    "Netwerkontwerp en integratie":
        "De structurele opzet van het spoornetwerk en de mate waarin dit fysiek en operationeel is geïntegreerd met andere vervoersmodaliteiten.",
    "Gebruikerservaring en kwaliteit":
        "De ervaren kwaliteit van het systeem vanuit het perspectief van de reiziger, inclusief comfort, gebruiksgemak en systeemimago.",
    "Bereikbaarheid van stations":
        "De mate waarin stations eenvoudig bereikbaar zijn met verschillende vervoerswijzen.",
    "Ruimtelijke ontwikkeling":
        "De ruimtelijke spreiding en intensiteit van functies rondom stations en de afstemming tussen ruimtegebruik en vervoer.",
    "Governance en implementatie":
        "De institutionele en organisatorische context die de coördinatie, besluitvorming en uitvoering van het spoorsysteem mogelijk maakt.",
}

factor_descriptions = {
    "Service- en systeemkenmerken": {
        "Dienstfrequentie": "De mate waarin hoge frequenties de wachttijd verkorten en de flexibiliteit en aantrekkelijkheid van het systeem vergroten.",
        "Reissnelheid": "De mate waarin het systeem korte reistijden tussen herkomsten en bestemmingen mogelijk maakt, onder andere door hoge rijsnelheden.",
        "Beschikbaarheid": "De mate waarin de dienst beschikbaar is gedurende de dag en week, zoals laat in de avond en weekenden.",
        "Betrouwbaarheid": "De mate waarin reistijden en dienstuitvoering punctueel, consistent en voorspelbaar zijn, en het systeem in staat is verstoringen op te vangen en ervan te herstellen.",
    },
    "Netwerkontwerp en integratie": {
        "Doorkoppeling": "De mate waarin diensten door stadscentra rijden en meerdere corridors met elkaar verbinden zonder dat overstappen nodig zijn.",
        "Afstemming van dienstregelingen en overstappen": "De mate waarin dienstregelingen en overstappen op elkaar zijn afgestemd om naadloze multimodale reizen mogelijk te maken, onafhankelijk van de frequentie.",
        "Ontvlechting van infrastructuur": "De mate waarin het systeem gebruikmaakt van eigen, gescheiden infrastructuur, waardoor interferentie met ander spoor- of wegverkeer wordt geminimaliseerd.",
        "Tarief- en ticketintegratie": "De mate waarin tarieven en ticketsystemen zijn geïntegreerd over modaliteiten en vervoerders, zodat drempelloos reizen mogelijk is.",
    },
    "Gebruikerservaring en kwaliteit": {
        "Operationele prestaties van materieel": "De mate waarin het ontwerp van voertuigen efficiënte exploitatie ondersteunt, waaronder snel afremmen en optrekken, hoge capaciteit, gelijkvloerse instap en deurconfiguratie.",
        "Systeemidentiteit en uitstraling": "De mate waarin het systeem een duidelijke, herkenbare en aantrekkelijke identiteit heeft die het onderscheidt van andere OV-diensten.",
        "Reizigerscomfort en gebruiksgemak": "De algehele reizigerservaring, inclusief comfort, duidelijke en actuele reisinformatie en het gemak van het navigeren en gebruiken van het systeem.",
    },
    "Bereikbaarheid van stations": {
        "Stationsdichtheid en -spreiding": "De mate waarin stations voldoende dicht en ruimtelijk goed verspreid zijn om brede toegang tot het netwerk te bieden.",
        "Loop- en fietsbereikbaarheid van stations": "De mate waarin stations goed bereikbaar zijn te voet en per fiets, inclusief de beschikbaarheid van voldoende stallingen.",
        "Autobereikbaarheid van stations": "De mate waarin stations parkeervoorzieningen bieden om de overstap van auto naar trein te faciliteren.",
    },
    "Ruimtelijke ontwikkeling": {
        "Dichtheid van herkomsten en bestemmingen": "De mate waarin bevolking en activiteiten geconcentreerd zijn rond stations en langs corridors.",
        "Afstemming tussen ruimtelijke ontwikkeling en vervoersinvesteringen": "De mate waarin ruimtelijke ontwikkeling en transportinfrastructuur in tijd, locatie en schaal op elkaar zijn afgestemd en elkaar versterken.",
        "Diversiteit van bestemmingen rond stations": "De mate waarin een mix van functies zoals werkgelegenheid, onderwijs, detailhandel en recreatie aanwezig is in stationsgebieden, waardoor meerdere reismotieven worden ondersteund.",
    },
    "Governance en implementatie": {
        "Samenwerking tussen vervoersorganisaties": "De mate van samenwerking tussen vervoerders en overheden bij planning, exploitatie en integratie van diensten.",
        "Rol van regionale overheden": "De mate waarin regionale of stedelijke overheden, ten opzichte van nationale overheden, regie voeren over ontwerp, financiering en integratie van het systeem.",
        "Institutionele integratie van mobiliteit en ruimtelijke ordening": "De mate waarin vervoersautoriteiten en ruimtelijke planners gezamenlijke besluitvorming, verantwoordelijkheden en langetermijnstrategieën delen om samenhangende uitkomsten te realiseren.",
    },
}

categories = {cat: list(f.keys()) for cat, f in factor_descriptions.items()}

scale = {
    "Gelijk belangrijk":             1,
    "Iets meer belangrijk":          2,
    "Enigszins meer belangrijk":     3,
    "Matig meer belangrijk":         4,
    "Duidelijk meer belangrijk":     5,
    "Aanzienlijk meer belangrijk":   6,
    "Sterk meer belangrijk":         7,
    "Veel meer belangrijk":          8,
    "Absoluut meer belangrijk":      9,
}
scale_labels = list(scale.keys())

# ─────────────────────────────────────────────
# STEP DEFINITIONS
# New order: select best+worst together, then bto, then otw
# ─────────────────────────────────────────────
cat_list = list(categories.keys())
N = len(cat_list)
STEP_INTRO            = 1
STEP_PERSONAL         = 2
STEP_CAT_SELECT       = 3        # best+worst category (separate page)
STEP_CAT_CMP          = 4        # category bto+otw comparisons (separate page)
# Per category: 2 pages each
# STEP_FACTOR_SEL_START + 2*i   = select best+worst for category i
# STEP_FACTOR_SEL_START + 2*i+1 = bto+otw comparisons for category i
STEP_FACTOR_SEL_START = 5
STEP_SUMMARY          = 5 + 2 * N
STEP_THANKYOU         = 5 + 2 * N + 1
TOTAL_STEPS           = STEP_SUMMARY  # progress bar goes up to summary only

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for _k, _v in [("step", STEP_INTRO), ("data", {}), ("errors", []), ("prev_step", -1)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────
def save_progress():
    data_json = json.dumps(st.session_state.data, ensure_ascii=False)
    tok = random.randint(0, 999999)
    st.components.v1.html(
        f"<script>/*{tok}*/try{{localStorage.setItem('bwm_data',{json.dumps(data_json)});"
        f"localStorage.setItem('bwm_step','{st.session_state.step}');}}catch(e){{}}</script>",
        height=0)

def clear_progress():
    st.components.v1.html(
        "<script>try{localStorage.removeItem('bwm_data');"
        "localStorage.removeItem('bwm_step');}catch(e){}</script>", height=0)

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

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

        # Category bto values
        for cat in cat_list:
            row.append(bto.get(cat, ""))

        # Category otw values
        for cat in cat_list:
            row.append(otw.get(cat, ""))

        # Factor best, worst, bto, otw per category
        for cat in cat_list:
            cd = fac.get(cat, {})
            row.append(cd.get("best", ""))
            row.append(cd.get("worst", ""))
            for f in categories[cat]:
                row.append(cd.get("best_to_others", {}).get(f, ""))
            for f in categories[cat]:
                row.append(cd.get("others_to_worst", {}).get(f, ""))

        # Write header row if sheet is empty
        if sheet.row_count == 0 or not sheet.row_values(1):
            header = [
                "Timestamp", "Naam", "Titel", "Organisatie", "Rol",
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
            sheet.append_row(header)

        sheet.append_row(row)
        return True

    except Exception as e:
        st.error(f"❌ Fout bij opslaan naar Google Sheets: {e}")
        return False

# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────
def next_step():
    st.session_state.step += 1
    st.session_state.errors = []

def prev_step():
    st.session_state.step -= 1
    st.session_state.errors = []

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
# SCROLL — unique token forces fresh iframe each time
# ─────────────────────────────────────────────
if st.session_state.step != st.session_state.prev_step:
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
    st.session_state.prev_step = st.session_state.step

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
    elif not current:
        st.caption("👆 Klik op een optie om de omschrijving te zien.")
    st.markdown("")
    return current

def scale_slider(label, key, saved_value=None):
    default = saved_value if saved_value in scale_labels else scale_labels[0]
    chosen = st.select_slider(label, options=scale_labels, value=default, key=key)
    st.caption(f"Numerieke waarde: **{scale[chosen]}**")
    return chosen

def compare_label(term_a, desc_a, term_b, desc_b):
    tip_a = tip_html(desc_a) if desc_a else ""
    tip_b = tip_html(desc_b) if desc_b else ""
    st.markdown(
        '<p class="bwm-cmp">Hoe veel belangrijker is '
        '<span class="ta">' + term_a + '</span>' + tip_a +
        ' dan <span class="tb">' + term_b + '</span>' + tip_b + '?</p>',
        unsafe_allow_html=True)

def image_placeholder():
    st.markdown(
        '<div class="img-placeholder">📷 Hier komt een afbeelding van de categorieën en factoren</div>',
        unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PROGRESS BAR + IMAGE PLACEHOLDER
# ─────────────────────────────────────────────
if st.session_state.step < STEP_THANKYOU:
    pct = min((st.session_state.step - 1) / max(TOTAL_STEPS - 1, 1), 1.0)
    st.progress(pct)
    st.caption(f"Voortgang: **{int(pct * 100)}%** voltooid")
    st.markdown("---")
    image_placeholder()

# ══════════════════════════════════════════════
# STEP 1: INTRODUCTIE
# ══════════════════════════════════════════════
if st.session_state.step == STEP_INTRO:
    st.title("🚆 Succesfactoren voor Voorstedelijk Spoorvervoer")
    st.subheader("Expertenquête — Best-Worst Methode (BWM)")
    st.markdown("""
**Welkom bij dit onderzoek.** U wordt gevraagd uw expertise in te zetten om de
relatieve belangrijkheid van factoren te beoordelen via de Best-Worst Methode.

### Werkwijze
1. De **meest belangrijke** factor/categorie aanwijzen
2. De **minst belangrijke** factor/categorie aanwijzen
3. **Best-to-others**: hoeveel belangrijker is de beste dan alle anderen?
4. **Others-to-worst**: hoeveel belangrijker is elke andere dan de slechtste?

### Categorieën & factoren
""")
    for cat, factors in categories.items():
        st.markdown(f"- **{cat}**: {', '.join(factors)}")
    st.info("💾 Uw voortgang wordt automatisch opgeslagen in uw browser.")
    st.button("Start enquête →", on_click=next_step, type="primary")

# ══════════════════════════════════════════════
# STEP 2: PERSOONLIJKE GEGEVENS
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_PERSONAL:
    st.title("Persoonlijke informatie")
    st.markdown("Verplichte velden zijn gemarkeerd met *")
    p = st.session_state.data.get("persoonlijk", {})
    naam        = st.text_input("Volledige naam *",      value=p.get("naam",""))
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
    st.session_state.data["persoonlijk"] = {
        "naam":naam,"titel":titel,"organisatie":organisatie,
        "rol":rol,"expertise":expertise,"opleiding":opleiding,"ervaring":ervaring}
    errors = []
    if not naam.strip():         errors.append("⚠️ Naam is verplicht.")
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
        st.markdown(f"Selecteer de **meest** en **minst belangrijke** factor binnen **{cat}**.")

        sel_key_b = f"best_f_sel_{cat}"
        if sel_key_b not in st.session_state:
            saved_b = st.session_state.data["factoren"][cat].get("best", None)
            st.session_state[sel_key_b] = saved_b if saved_b in factors else None

        st.markdown("**⭐ Meest belangrijke factor**")
        best_f = card_select(factors, sel_key_b, descriptions=factor_descriptions.get(cat, {}))
        st.session_state.data["factoren"][cat]["best"] = best_f

        st.markdown("---")
        remaining_f = [f for f in factors if f != best_f]
        sel_key_w = f"worst_f_sel_{cat}"
        if sel_key_w not in st.session_state:
            saved_w = st.session_state.data["factoren"][cat].get("worst", None)
            st.session_state[sel_key_w] = saved_w if saved_w in remaining_f else None

        st.markdown("**⚪ Minst belangrijke factor**")
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
                st.write(f"- {k}: {v} ({scale.get(v,'?')})")
        with col2:
            st.markdown("**Others-to-worst:**")
            for k, v in st.session_state.data.get("categorie_others_to_worst", {}).items():
                st.write(f"- {k}: {v} ({scale.get(v,'?')})")

    for cat in cat_list:
        cd = st.session_state.data.get("factoren", {}).get(cat, {})
        with st.expander(f"🔍 {cat}", expanded=False):
            st.write(f"**Meest belangrijk**: {cd.get('best','—')} | **Minst belangrijk**: {cd.get('worst','—')}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Best-to-others:**")
                for k, v in cd.get("best_to_others", {}).items():
                    st.write(f"- {k}: {v} ({scale.get(v,'?')})")
            with col2:
                st.markdown("**Others-to-worst:**")
                for k, v in cd.get("others_to_worst", {}).items():
                    st.write(f"- {k}: {v} ({scale.get(v,'?')})")

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
    if col2.button("📨 Verzend enquête", type="primary"):
        with st.spinner("Antwoorden opslaan..."):
            success = save_to_sheets(st.session_state.data)
        if success:
            clear_progress()
            st.session_state.step = STEP_THANKYOU
            st.rerun()
        else:
            with st.expander("📋 Ruwe data (voor ontwikkeling)", expanded=False):
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
    succesfactoren voor stadsgewestelijk spoorvervoer.
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:2rem 0;">
  <p style="color:#64748b;font-size:0.95rem;">
    Heeft u vragen over het onderzoek? Neem dan contact op via:<br>
    <strong>📧 <a href="mailto:l.spijker@student.utwente.nl" style="color:#3b82f6;">
    l.m.spijker@student.utwente.nl</a></strong>
  </p>
  <p style="color:#94a3b8;font-size:0.9rem;margin-top:2rem;">
    U kunt dit tabblad nu sluiten.
  </p>
</div>
""", unsafe_allow_html=True)
