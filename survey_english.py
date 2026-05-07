# -*- coding: utf-8 -*-
"""BWM Survey — English version"""

import streamlit as st
import json
import random
import math
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ─────────────────────────────────────────────
# IMAGE FILENAMES — edit these to match your PNG files
# Place all images in the "images" subfolder next to this script
# ─────────────────────────────────────────────
IMAGES = {
    "intro":        "factors_en_new.drawio.png",   # Sidebar image on welcome page
    "categories":   "categories.png",        # Category selection + comparison pages
    "category_1":   "systemcharacteristics.drawio.png",        # System characteristics
    "category_2":   "integration.drawio.png",        # Integration with urban networks
    "category_3":   "userexperience.drawio.png",        # User experience
    "category_4":   "accessibility.drawio.png",        # Accessibility to stations
    "category_5":   "landuse.drawio.png",        # Land use and spatial development
}


st.set_page_config(page_title="BWM Survey", layout="wide", page_icon="🚆")

st.markdown("""
<style>
    .block-container { max-width: 800px; margin: 0 auto; padding-top: 2rem; }
    div[data-testid="stButton"] button[kind="secondary"] {
        background: #ffffff !important; border: 1.5px solid #e2e8f0 !important;
        border-radius: 8px !important; color: #1e293b !important;
        font-weight: 400 !important; text-align: left !important;
        padding: 10px 16px !important; box-shadow: none !important;
        width: 100% !important; justify-content: flex-start !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: #f8fafc !important; border-color: #94a3b8 !important;
        color: #1e293b !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: #eff6ff !important; border: 1.5px solid #3b82f6 !important;
        border-radius: 8px !important; color: #1e293b !important;
        font-weight: 600 !important; text-align: left !important;
        padding: 10px 16px !important; box-shadow: none !important;
        width: 100% !important; justify-content: flex-start !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: #dbeafe !important; border-color: #2563eb !important;
        color: #1e293b !important;
    }
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
        visibility:hidden; opacity:0; background:#1e293b; color:#f1f5f9;
        font-size:0.82rem; line-height:1.5; border-radius:6px;
        padding:9px 13px; position:absolute; z-index:9999;
        left:24px; top:-6px; width:320px;
        box-shadow:0 4px 16px rgba(0,0,0,0.22);
        transition:opacity 0.15s ease; pointer-events:none;
    }
    .tip:hover .tip-text { visibility:visible; opacity:1; }
    .bwm-cmp { font-size:0.97rem; margin-bottom:4px; color:#1e293b; }
    .bwm-cmp .ta { font-weight:600; }
    .bwm-cmp .tb { color:#64748b; }
    .img-placeholder {
        width:100%; height:180px; background:#f1f5f9;
        border:2px dashed #cbd5e1; border-radius:8px;
        display:flex; align-items:center; justify-content:center;
        color:#94a3b8; font-size:0.9rem; margin-bottom:1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA — English categories and factors
# ─────────────────────────────────────────────
category_descriptions = {
    "System characteristics":
        "The operational performance of the rail system, including service frequency, travel time, reliability and service span.",
    "Integration with urban networks":
        "The extent to which the rail system is physically and operationally integrated with urban public transport networks.",
    "User experience":
        "The perceived quality of the system from the passenger's perspective, including information, identity, affordability and comfort.",
    "Accessibility to stations":
        "The extent to which stations are easily reachable by various modes of transport.",
    "Land use and spatial development":
        "The spatial distribution and intensity of functions around stations and the alignment between land use and transport.",
}

factor_descriptions = {
    "System characteristics": {
        "Service frequency":
            "The extent to which high service frequencies reduce waiting time and increase flexibility.",
        "Travel time":
            "The extent to which the system enables short travel times between origins and destinations.",
        "Reliability":
            "The extent to which travel times and service operations are punctual, consistent and predictable.",
        "Service span":
            "The extent to which the service is available throughout the day and week, such as late at night or in weekends.",
    },
    "Integration with urban networks": {
        "Through-routing in urban areas":
            "The extent to which services provide direct connections across urban areas, minimizing the need for transfers.",
        "Transfer coordination with urban PT":
            "The extent to which schedules and physical transfers are aligned, independent of service frequency.",
        "Fare and ticket integration with urban PT":
            "The extent to which fare structures and ticketing systems are integrated across modes and operators.",
    },
    "User experience": {
        "Travel information":
            "The extent to which clear and real-time travel information is available online and at stations, and navigation is easy.",
        "System identity":
            "The extent to which the system has a clear, recognizable, and attractive identity that distinguishes it from other rail services.",
        "Affordability":
            "The extent to which public transport fares are affordable and competitive for users.",
        "Comfort":
            "The extent to which a high-quality passenger experience is provided (vehicles and stations), including capacity, safety and cleanliness.",
    },
    "Accessibility to stations": {
        "Station density and distribution":
            "The extent to which stations are sufficiently dense and well distributed spatially to provide broad access to the network.",
        "Walking and cycling accessibility to stations":
            "The extent to which stations are easily accessible by walking and cycling, including the availability of sufficient bicycle parking.",
        "Car parking at stations (P+R)":
            "The extent to which stations provide parking facilities to facilitate car-to-rail transfers.",
    },
    "Land use and spatial development": {
        "Density around stations":
            "The extent to which population and activities are concentrated around stations and along corridors.",
        "Coordination of land use and transport":
            "The extent to which land development and the transport network are spatially and functionally aligned.",
        "Mixed land use around stations":
            "The extent to which a mix of activities such as employment, education, retail, and leisure is present within station areas, supporting multiple trip purposes.",
    },
}

categories = {cat: list(f.keys()) for cat, f in factor_descriptions.items()}

scale = {
    "Slightly more important":      2,
    "Somewhat more important":      3,
    "Moderately more important":    4,
    "Clearly more important":       5,
    "Considerably more important":  6,
    "Absolutely more important":    7,
}
scale_labels = list(scale.keys())

# ─────────────────────────────────────────────
# STEP DEFINITIONS
# ─────────────────────────────────────────────
cat_list = list(categories.keys())
N = len(cat_list)
STEP_INTRO            = 1
STEP_CONSENT          = 2
STEP_PERSONAL         = 3
STEP_CAT_SELECT       = 4
STEP_CAT_CMP          = 5
STEP_FACTOR_SEL_START = 6
STEP_SUMMARY          = 6 + 2 * N
STEP_THANKYOU         = 6 + 2 * N + 1
TOTAL_STEPS           = STEP_SUMMARY

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for _k, _v in [("step", STEP_INTRO), ("data", {}), ("errors", []), ("prev_step", -1)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

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

def save_to_sheets(data: dict):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet  = client.open_by_url(st.secrets["sheet_url"]).sheet1

        p    = data.get("persoonlijk", {})
        bto  = data.get("categorie_best_to_others", {})
        otw  = data.get("categorie_others_to_worst", {})
        fac  = data.get("factoren", {})

        submit_time  = datetime.now()
        start_time   = st.session_state.get("start_time", submit_time)
        duration_min = round((submit_time - start_time).total_seconds() / 60, 1)

        row = [
            st.session_state.get("respondent_id", ""),
            submit_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration_min,
            "EN",
            p.get("naam", ""), p.get("titel", ""), p.get("organisatie", ""),
            p.get("rol", ""), p.get("expertise", ""),
            p.get("opleiding", ""), p.get("ervaring", ""),
            data.get("categorie_best", ""), data.get("categorie_worst", ""),
            data.get("opmerkingen", ""),
        ]
        def to_num(label):
            """Convert linguistic scale label to numeric value, or return as-is."""
            return scale.get(label, label) if label else ""

        for cat in cat_list:
            row.append(to_num(bto.get(cat, "")))
        for cat in cat_list:
            row.append(to_num(otw.get(cat, "")))
        for cat in cat_list:
            cd = fac.get(cat, {})
            row.append(cd.get("best", ""))
            row.append(cd.get("worst", ""))
            for f in categories[cat]:
                row.append(to_num(cd.get("best_to_others", {}).get(f, "")))
            for f in categories[cat]:
                row.append(to_num(cd.get("others_to_worst", {}).get(f, "")))

        # Get all non-empty rows to reliably detect if header exists
        all_rows = sheet.get_all_values()
        non_empty = [r for r in all_rows if any(c.strip() for c in r)]
        if not non_empty:
            header = ["Respondent ID", "Timestamp", "Duration (min)", "Language",
                      "Name", "Title", "Organisation", "Role", "Expertise",
                      "Education", "Experience",
                      "Category Best", "Category Worst", "Comments"]
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
        st.error(f"❌ Error saving to Google Sheets: {e}")
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
        col1.button("← Previous", on_click=prev_step)
    col2.button("Next →", on_click=next_step,
                disabled=not can_proceed, type="primary")

# ─────────────────────────────────────────────
# SCROLL
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
    descriptions = descriptions or {}
    if state_key not in st.session_state or st.session_state[state_key] not in options:
        if state_key == "best_cat_sel":
            saved = st.session_state.data.get("categorie_best", None)
        elif state_key == "worst_cat_sel":
            saved = st.session_state.data.get("categorie_worst", None)
        else:
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
        st.caption("👆 Click an option to see its description.")
    st.markdown("")
    return current

def scale_slider(label, key, saved_value=None):
    default = saved_value if saved_value in scale_labels else scale_labels[0]
    chosen = st.select_slider(label, options=scale_labels, value=default, key=key)
    st.caption(f"Numerical value: **{scale[chosen]}**")
    return chosen

def compare_label(term_a, desc_a, term_b, desc_b):
    tip_a = tip_html(desc_a) if desc_a else ""
    tip_b = tip_html(desc_b) if desc_b else ""
    st.markdown(
        '<p class="bwm-cmp">How much more important is '
        '<span class="ta">' + term_a + '</span>' + tip_a +
        ' than <span class="tb">' + term_b + '</span>' + tip_b + '?</p>',
        unsafe_allow_html=True)

def show_page_image(key: str, sidebar: bool = False):
    """
    Display a PNG image by its key from the IMAGES dict above.
    Images are loaded from the "images" subfolder next to this script.
    """
    from pathlib import Path
    filename = IMAGES.get(key, "")
    if not filename:
        return
    path = Path(__file__).parent / "images" / filename
    if path.exists():
        if sidebar:
            with st.sidebar:
                st.image(str(path), use_container_width=True)
        else:
            st.image(str(path), use_container_width=True)
    else:
        st.markdown(
            f'<div class="img-placeholder">📷 Afbeelding niet gevonden: images/{filename}</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PROGRESS BAR
# ─────────────────────────────────────────────
if st.session_state.step < STEP_THANKYOU:
    pct = min((st.session_state.step - 1) / max(TOTAL_STEPS - 1, 1), 1.0)
    st.progress(pct)
    st.caption(f"Progress: **{int(pct * 100)}%** completed")
    st.markdown("---")

# ══════════════════════════════════════════════
# STEP 1: INTRODUCTION
# ══════════════════════════════════════════════
if st.session_state.step == STEP_INTRO:
    show_page_image("intro", sidebar=True)
    st.title("🚆 Success Factors for Suburban Rail Transport")
    st.subheader("Expert Survey — Best-Worst Method (BWM)")
    st.markdown("""
**Welcome to this research survey.** You are asked to apply your expertise to assess
the relative importance of factors for successful suburban rail transport using the
Best-Worst Method (BWM).

### How it works
For each level you will be asked to:
1. Select the **most important** factor/category
2. Select the **least important** factor/category
3. **Best-to-others**: how much more important is the best compared to all others?
4. **Others-to-worst**: how much more important is each other compared to the worst?

### Categories & factors
""")
    for cat, factors in categories.items():
        st.markdown(f"- **{cat}**: {', '.join(factors)}")
    st.button("Start survey →", on_click=next_step, type="primary")

# ══════════════════════════════════════════════
# STEP 2: CONSENT
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_CONSENT:
    st.title("📋 Informed Consent & Privacy")
    st.markdown("""
### About this research

This survey is conducted by **Luuk Spijker** as part of a graduation thesis at the
**University of Twente** (Faculty of ITC / Civil Engineering).

The aim is to determine the relative importance of success factors for suburban rail
transport using the Best-Worst Method (BWM).
""")
    st.markdown("---")
    st.subheader("🔒 How we handle your data")
    st.markdown("""
- **What is collected:** your role, organisation, field of expertise, and your survey responses.
  Your name is **optional** and not required to participate.
- **Storage:** all data is stored in a secured Google Workspace account linked to the
  University of Twente (@utwente.nl).
- **Access:** only the researcher (Luuk Spijker) and the supervising professor have
  access to the raw data.
- **Retention:** all collected data will be deleted after completion and approval of
  the research (no later than October 2026).
- **Legal basis:** participation is voluntary and based on your consent (GDPR Art. 6(1)(a)).
- **Right to withdraw:** you may withdraw your participation at any time and request
  deletion of your data by contacting **l.m.spijker@student.utwente.nl**.
    st.markdown("---")
    st.subheader("✅ Consent")
    st.markdown("Please tick both boxes below to proceed with the survey.")
    c1 = st.checkbox(
        "I have read and understood the information above, and I give my consent "
        "to the processing of my responses for the purposes of this research.")
    c2 = st.checkbox(
        "I understand that my participation is voluntary and that I may withdraw "
        "my consent at any time by contacting the researcher.")
    all_consent = c1 and c2
    if not all_consent:
        st.info("Please tick both boxes to continue.")
    col1, col2 = st.columns(2)
    col1.button("← Previous", on_click=prev_step)
    col2.button("Next →", on_click=next_step,
                disabled=not all_consent, type="primary")

# ══════════════════════════════════════════════
# STEP 3: PERSONAL INFORMATION
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_PERSONAL:
    st.title("Personal information")
    st.markdown("Fields marked with * are required. Your name is optional.")
    p = st.session_state.data.get("persoonlijk", {})
    naam        = st.text_input("Full name (optional)",     value=p.get("naam",""))
    titel       = st.text_input("Title(s)",                 value=p.get("titel",""))
    organisatie = st.text_input("Organisation *",           value=p.get("organisatie",""))
    expertise   = st.text_input("Field of expertise",       value=p.get("expertise",""))
    rol_opts = ["-- Select --","Researcher","Policy maker","Consultant",
                "Transport operator","Government","Other"]
    rol = st.selectbox("Role *", rol_opts,
        index=rol_opts.index(p.get("rol","-- Select --")) if p.get("rol") in rol_opts else 0)
    opl_opts = ["-- Select --","Bachelor","Master","PhD","Other"]
    opleiding = st.selectbox("Highest level of education", opl_opts,
        index=opl_opts.index(p.get("opleiding","-- Select --")) if p.get("opleiding") in opl_opts else 0)
    erv_opts = ["-- Select --","0-2 years","3-5 years","6-10 years","10+ years"]
    ervaring = st.selectbox("Years of relevant experience", erv_opts,
        index=erv_opts.index(p.get("ervaring","-- Select --")) if p.get("ervaring") in erv_opts else 0)
    def clean(v, placeholder="-- Selecteer --"):
        return "" if v == placeholder else v
    st.session_state.data["persoonlijk"] = {
        "naam":naam,"titel":titel,"organisatie":organisatie,
        "rol":clean(rol),"expertise":expertise,
        "opleiding":clean(opleiding),"ervaring":clean(ervaring)}
    errors = []
    if not organisatie.strip():  errors.append("⚠️ Organisation is required.")
    if rol == "-- Select --":    errors.append("⚠️ Please select a role.")
    show_errors()
    save_progress()
    nav_buttons(can_proceed=len(errors)==0)

# ══════════════════════════════════════════════
# STEP 4: SELECT BEST + WORST CATEGORY
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_CAT_SELECT:
    st.title("Category comparison — Step 1 of 2")
    show_page_image("categories")
    st.markdown("Select the category you consider **most** and **least important** for the success of suburban rail transport.")

    if "best_cat_sel" not in st.session_state:
        saved_bc = st.session_state.data.get("categorie_best", None)
        st.session_state["best_cat_sel"] = saved_bc if saved_bc in cat_list else None

    st.markdown("**⭐ Most important category**")
    st.caption("_💡 Click an option to view its description._")
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

    st.markdown("**⚪ Least important category**")
    st.caption("_💡 Click an option to view its description._")
    worst_cat = card_select(remaining, "worst_cat_sel", descriptions=category_descriptions)
    if worst_cat:
        st.session_state.data["categorie_worst"] = worst_cat

    errors = []
    if not best_cat:  errors.append("⚠️ Please select the most important category.")
    if not worst_cat: errors.append("⚠️ Please select the least important category.")
    if best_cat and worst_cat and worst_cat == best_cat:
        errors.append("⚠️ The least important category cannot be the same as the most important.")
    show_errors()
    save_progress()
    nav_buttons(can_proceed=len(errors)==0)

# ══════════════════════════════════════════════
# STEP 5: CATEGORY COMPARISONS (BTO + OTW)
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_CAT_CMP:
    best_cat  = st.session_state.data.get("categorie_best", cat_list[0])
    worst_cat = st.session_state.data.get("categorie_worst", cat_list[-1])
    st.title("Category comparison — Step 2 of 2")
    show_page_image("categories")

    st.subheader(f"How much more important is '{best_cat}' than the other categories?")
    bto = st.session_state.data.get("categorie_best_to_others", {})
    for c in [x for x in cat_list if x != best_cat]:
        compare_label(best_cat, category_descriptions.get(best_cat,""),
                      c,        category_descriptions.get(c,""))
        bto[c] = scale_slider("", key=f"bto_cat_{c}", saved_value=bto.get(c))
        st.markdown("")
    st.session_state.data["categorie_best_to_others"] = bto

    st.markdown("---")
    st.subheader(f"How much more important are the other categories than '{worst_cat}'?")
    otw = st.session_state.data.get("categorie_others_to_worst", {})
    for c in [x for x in cat_list if x != worst_cat]:
        compare_label(c,         category_descriptions.get(c,""),
                      worst_cat, category_descriptions.get(worst_cat,""))
        otw[c] = scale_slider("", key=f"otw_cat_{c}", saved_value=otw.get(c))
        st.markdown("")
    st.session_state.data["categorie_others_to_worst"] = otw
    save_progress()
    nav_buttons()

# ══════════════════════════════════════════════
# STEPS 6..6+2N-1: PER CATEGORY (2 PAGES EACH)
# ══════════════════════════════════════════════
elif STEP_FACTOR_SEL_START <= st.session_state.step < STEP_SUMMARY:
    offset    = st.session_state.step - STEP_FACTOR_SEL_START
    cat_index = offset // 2
    page_type = offset % 2
    cat       = cat_list[cat_index]
    factors   = categories[cat]

    if "factoren" not in st.session_state.data:
        st.session_state.data["factoren"] = {}
    if cat not in st.session_state.data["factoren"]:
        st.session_state.data["factoren"][cat] = {}

    if page_type == 0:
        st.title(f"Category {cat_index + 1} of {N}: {cat}")
        show_page_image(f"category_{cat_index + 1}")
        st.markdown(f"Select the **most** and **least important** factor within **{cat}**.")

        sel_key_b = f"best_f_sel_{cat}"
        if sel_key_b not in st.session_state:
            saved_b = st.session_state.data["factoren"][cat].get("best", None)
            st.session_state[sel_key_b] = saved_b if saved_b in factors else None

        st.markdown("**⭐ Most important factor**")
        st.caption("_💡 Click an option to view its description._")
        best_f = card_select(factors, sel_key_b, descriptions=factor_descriptions.get(cat,{}))
        st.session_state.data["factoren"][cat]["best"] = best_f

        st.markdown("---")
        remaining_f = [f for f in factors if f != best_f] if best_f else factors
        sel_key_w = f"worst_f_sel_{cat}"
        if sel_key_w not in st.session_state:
            saved_w = st.session_state.data["factoren"][cat].get("worst", None)
            st.session_state[sel_key_w] = saved_w if saved_w in remaining_f else None
        if st.session_state.get(sel_key_w) not in remaining_f:
            st.session_state[sel_key_w] = None

        st.markdown("**⚪ Least important factor**")
        st.caption("_💡 Click an option to view its description._")
        worst_f = card_select(remaining_f, sel_key_w, descriptions=factor_descriptions.get(cat,{}))
        st.session_state.data["factoren"][cat]["worst"] = worst_f

        errors = []
        if not best_f:  errors.append("⚠️ Please select the most important factor.")
        if not worst_f: errors.append("⚠️ Please select the least important factor.")
        if best_f and worst_f and worst_f == best_f:
            errors.append(f"⚠️ The least important factor cannot be the same as the most important ({best_f}).")
        show_errors()
        save_progress()
        nav_buttons(can_proceed=len(errors)==0)

    else:
        cat_data = st.session_state.data["factoren"][cat]
        best_f   = cat_data.get("best", factors[0])
        worst_f  = cat_data.get("worst", factors[-1])

        st.title(f"Category {cat_index + 1} of {N}: {cat} — Comparisons")
        show_page_image(f"category_{cat_index + 1}")

        st.subheader(f"How much more important is '{best_f}' than the other factors?")
        bto_f = cat_data.get("best_to_others", {})
        for f in [x for x in factors if x != best_f]:
            compare_label(best_f, factor_descriptions.get(cat,{}).get(best_f,""),
                          f,      factor_descriptions.get(cat,{}).get(f,""))
            bto_f[f] = scale_slider("", key=f"bto_{cat}_{f}", saved_value=bto_f.get(f))
            st.markdown("")
        st.session_state.data["factoren"][cat]["best_to_others"] = bto_f

        st.markdown("---")
        st.subheader(f"How much more important are the other factors than '{worst_f}'?")
        otw_f = cat_data.get("others_to_worst", {})
        for f in [x for x in factors if x != worst_f]:
            compare_label(f,       factor_descriptions.get(cat,{}).get(f,""),
                          worst_f, factor_descriptions.get(cat,{}).get(worst_f,""))
            otw_f[f] = scale_slider("", key=f"otw_{cat}_{f}", saved_value=otw_f.get(f))
            st.markdown("")
        st.session_state.data["factoren"][cat]["others_to_worst"] = otw_f
        save_progress()
        nav_buttons()

# ══════════════════════════════════════════════
# SUMMARY & SUBMIT
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_SUMMARY:
    st.title("✅ Review & Submit")
    st.markdown("Please review your answers below. You can go back to make changes.")

    with st.expander("👤 Personal information", expanded=False):
        for k, v in st.session_state.data.get("persoonlijk", {}).items():
            st.write(f"**{k.capitalize()}**: {v}")

    with st.expander("📊 Category comparisons", expanded=True):
        bc = st.session_state.data.get("categorie_best", "—")
        wc = st.session_state.data.get("categorie_worst", "—")
        st.write(f"**Most important**: {bc} | **Least important**: {wc}")
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
            st.write(f"**Most important**: {cd.get('best','—')} | **Least important**: {cd.get('worst','—')}")
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
    st.subheader("💬 Comments & recommendations")
    st.markdown("Do you have any comments, questions or recommendations regarding this research?")
    opmerkingen = st.text_area(
        "Your comments (optional)",
        value=st.session_state.data.get("opmerkingen", ""),
        height=120,
        placeholder="Type any comments here...")
    st.session_state.data["opmerkingen"] = opmerkingen

    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.button("← Previous", on_click=prev_step)
    already_submitted = st.session_state.get("submitted", False)
    if already_submitted:
        st.success("✅ Your responses have been submitted. You can close this tab.")
    elif col2.button("📨 Submit survey", type="primary"):
        with st.spinner("Saving responses..."):
            success = save_to_sheets(st.session_state.data)
        if success:
            st.session_state.submitted = True
            clear_progress()
            st.session_state.step = STEP_THANKYOU
            st.rerun()
        else:
            st.error("❌ Something went wrong. Please try again or contact l.m.spijker@student.utwente.nl")
            with st.expander("📋 Raw data (backup — copy this if needed)", expanded=True):
                st.json(st.session_state.data)

# ══════════════════════════════════════════════
# THANK-YOU PAGE
# ══════════════════════════════════════════════
elif st.session_state.step == STEP_THANKYOU:
    st.balloons()
    st.markdown("""
<div style="text-align:center;padding:3rem 1rem;">
  <div style="font-size:4rem;margin-bottom:1rem;"></div>
  <h1 style="color:#1e293b;">Thank you for your participation!</h1>
  <p style="font-size:1.1rem;color:#475569;max-width:500px;margin:1rem auto 2rem;">
    Your responses have been successfully saved and contribute to the research into
    success factors for suburban rail transport.
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:2rem 0;">
  <p style="color:#64748b;font-size:0.95rem;">
    Do you have any questions about the research? Please contact:<br>
    <strong>📧 <a href="mailto:l.spijker@student.utwente.nl" style="color:#3b82f6;">
    l.spijker@student.utwente.nl</a></strong>
  </p>
  <p style="color:#94a3b8;font-size:0.9rem;margin-top:2rem;">
    You may now close this tab.
  </p>
</div>
""", unsafe_allow_html=True)
