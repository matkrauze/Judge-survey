"""
GCB Judge Survey App
Streamlit + Supabase backend
Token-based access: each lawyer gets a unique link ?token=xxx
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timezone
import uuid

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="General Court Barometer – Judge Survey",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Supabase client ────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

sb = get_supabase()

# ── Judge list (from your CSV, hardcoded for reliability) ──────────────────────
JUDGES = [
    "Azizi, Josef", "Brkan, Maja", "Buttigieg, Eugène", "Cassagnabère, Hervé",
    "Collins, Anthony", "Cooke, John", "Cremona, Ena", "Czúcz, Ottó",
    "da Silva Passos, Ricardo", "De Baere, Geert", "Dehousse, Franklin",
    "Dimitrakopoulos, Ioannis", "Forwood, Nicholas", "Frendo, Ramona",
    "Gâlea, Ion", "García-Gallardo, Ramón", "García-Valdecasas y Fernández, Rafael",
    "Gratsias, Dimitrios", "Hesse, Gerhard", "Jaeger, Marc", "José Costeira, Maria",
    "Jürimäe, Küllike", "Kancheva, Mariyana", "Kanninen, Heikki",
    "Kecsmár, Krisztián", "Kingston, Suzanne", "Knez, Jana", "Kornezov, Alexander",
    "Kowalik-Bańczyk, Krystyna", "Kreuschitz, Viktor", "Kukovec, Damjan",
    "Kumin, Andreas", "Labucka, Ingrīda", "Laitenberger, Johannes", "Legal, Hubert",
    "Lindh, Pernilla", "Loot, Heiki", "Lourdes Arastey Sahún, María",
    "Luis da Cruz Vilaca, Jose", "Lukas Kalėda, Saulius", "Mac Eochaidh, Colm",
    "Madise, Lauri", "Marcoulli, Anna", "Mastroianni, Roberto", "Mengozzi, Paolo",
    "Mertens de Wilmars, Frédéric", "Meyer, Raphaël", "Milanesi, Enzo", "Motoc, Iulia",
    "Nihoul, Paul", "Nõmm, Iko", "Norkus, Rimvydas", "Ó Caoimh, Aindrias",
    "Öberg, Ulf", "Palesne, Nina", "Papasavvas, Savvas", "Pavlík, Petr",
    "Pelikánová, Irena", "Pérez de Nanclares, José", "Perišin, Tamara",
    "Petrlík, David", "Pirrung, Jörg", "Półtorak, Nina", "Porchia, Ornella",
    "Prek, Miro", "Pucurull, Miguel", "Reine, Inga", "Ribeiro, Maria",
    "Ricziová, Beatrix", "Riitta Pynnä, Tuula", "Schwarcz, Juraj",
    "Škvařilová-Pelzl, Petra", "Spangsberg Grønfeldt, Louise", "Spielmann, Dean",
    "Spineanu-Matei, Octavia", "Stancu, Mirela", "Steinfatt, Gabriele",
    "Sulyok, Gábor", "Šváby, Daniel", "Svenningsen, Jesper", "Szívós, Mária",
    "Tichy-Fisslberger, Elisabeth", "Tiili, Virpi", "Tomljenović, Vesna",
    "Tóth, Tihamér", "Trstenjak, Verica", "Truchot, Laurent", "Vadapalas, Vilenas",
    "Valasidis, William", "van der Woude, Marc", "Verschuur, Steven",
    "Vesterdorf, Bo", "Vilaras, Michail", "von Danwitz, Thomas",
    "W. H. Meij, Arjen", "Wahl, Nils", "Wetter, Carl",
    "Wiszniewska-Białecka, Irena", "Zilgalvis, Pēteris",
]

CAPACITIES = [
    "Private practice",
    "Private practice – appeared before the General Court",
    "In-house lawyer",
    "In-house lawyer – appeared before the General Court",
    "Référendaire at the General Court",
    "Lawyer at an EU institution or EU agency",
    "Lawyer at an EU institution or EU agency – appeared before the General Court",
    "Lawyer for a Member State government",
    "Lawyer for a Member State government – appeared before the General Court",
    "Academic",
]

FAMILIARITY_SOURCES = [
    "In court – through appearances before that judge",
    "In court – other than through appearances (e.g. judicial assistant)",
    "Outside of court (conferences, academic collaboration, etc.)",
    "Private setting (not related to the professional sphere)",
    "Indirect (e.g. through judgements, articles, speeches, etc.)",
]

ECONOMIC_REASONING_PREAMBLE = """
**Definition of economic reasoning used in this survey**

For the purposes of this survey, *economic reasoning* refers to the use of economic concepts
and principles — such as incentives, costs and benefits, efficiency of regulation, financial
stability, moral hazard, information asymmetry, and regulatory impact — to inform judicial
decision-making.

Judges may apply economic reasoning in various ways, including:
- Evaluating the consequences of legal rules for market outcomes, competition, or consumer welfare
- Considering the incentives created by legal decisions for firms, consumers, or governments
- Weighing the costs and benefits of regulatory interventions
- Referring to economic models or ideas (e.g., market failure, externalities, monopolistic behaviour)
- Balancing competing interests such as consumer welfare and financial stability

Note: Economic reasoning need not involve formal economic models or technical language. It
includes broader economic intuition and reasoning about how laws affect behaviour, incentives,
and outcomes of economic actors.
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
def now_utc():
    return datetime.now(timezone.utc).isoformat()

def get_respondent(token: str):
    res = sb.table("respondents").select("*").eq("token", token).execute()
    return res.data[0] if res.data else None

def get_background(respondent_id: str):
    res = sb.table("respondent_background").select("*").eq("respondent_id", respondent_id).execute()
    return res.data[0] if res.data else None

def get_judge_selections(respondent_id: str):
    res = sb.table("judge_selections").select("judge_name").eq("respondent_id", respondent_id).execute()
    return [r["judge_name"] for r in res.data]

def get_familiarity(respondent_id: str, judge_name: str):
    res = (sb.table("judge_familiarity").select("*")
           .eq("respondent_id", respondent_id).eq("judge_name", judge_name).execute())
    return res.data[0] if res.data else None

def get_responses_for_judge(respondent_id: str, judge_name: str):
    res = (sb.table("responses").select("*")
           .eq("respondent_id", respondent_id).eq("judge_name", judge_name).execute())
    return {r["question_num"]: r for r in res.data}

def upsert_response(respondent_id: str, judge_name: str, q_num: int,
                    answer_numeric=None, answer_text=None):
    sb.table("responses").upsert({
        "respondent_id": respondent_id,
        "judge_name": judge_name,
        "question_num": q_num,
        "answer_numeric": answer_numeric,
        "answer_text": answer_text,
        "submitted_at": now_utc(),
    }, on_conflict="respondent_id,judge_name,question_num").execute()

def count_completed_judges(respondent_id: str, selected_judges: list) -> int:
    """Count judges where all 12 questions have been answered."""
    completed = 0
    for judge in selected_judges:
        resp = get_responses_for_judge(respondent_id, judge)
        if len(resp) == 12:
            completed += 1
    return completed

# ── Token from URL ─────────────────────────────────────────────────────────────
params = st.query_params
token = params.get("token", "")

# ── Main app ───────────────────────────────────────────────────────────────────
st.title("⚖️ General Court Barometer")
st.markdown("*Judge Survey — KU Leuven PhD Research*")
st.markdown("---")

# ── No token: show instructions ────────────────────────────────────────────────
if not token:
    st.warning("⚠️ No access token found in the URL.")
    st.markdown("""
    This survey is accessed via a personalised link sent to you by email.
    If you believe you should have received an invitation, please contact the researcher.

    **Privacy notice:** Your responses are stored securely in an EU-hosted database
    (AWS eu-west-1, Ireland). Data is processed under KU Leuven's GDPR research framework.
    You may request deletion of your data at any time by contacting the researcher.
    """)
    st.stop()

# ── Look up respondent ─────────────────────────────────────────────────────────
respondent = get_respondent(token)
if not respondent:
    st.error("❌ Invalid or expired access token. Please check the link in your invitation email.")
    st.stop()

rid = respondent["id"]
first_name = respondent.get("first_name") or respondent["full_name"].split()[0]

# Mark survey started
if not respondent.get("survey_started_at"):
    sb.table("respondents").update({"survey_started_at": now_utc()}).eq("id", rid).execute()

# ── STAGE tracking in session state ───────────────────────────────────────────
# Stages: "background" → "judge_selection" → "familiarity" → "questions" → "done"
if "stage" not in st.session_state:
    # Resume from where they left off
    bg = get_background(rid)
    selections = get_judge_selections(rid)
    if not bg:
        st.session_state.stage = "background"
    elif not selections:
        st.session_state.stage = "judge_selection"
    else:
        # Check if all selected judges are fully answered
        completed = count_completed_judges(rid, selections)
        if completed == len(selections):
            st.session_state.stage = "done"
        else:
            st.session_state.stage = "questions"
            st.session_state.selected_judges = selections
            # Find first incomplete judge
            for j in selections:
                resp = get_responses_for_judge(rid, j)
                if len(resp) < 12:
                    st.session_state.current_judge_idx = selections.index(j)
                    break

# ── STAGE 1: Background ────────────────────────────────────────────────────────
if st.session_state.stage == "background":
    st.markdown(f"### Welcome, {first_name}!")
    st.markdown("""
    Thank you for participating in this survey on the use of economic reasoning
    by General Court judges. Your responses are confidential and will be used
    solely for PhD research purposes at KU Leuven.

    This should take approximately **15–30 minutes** depending on how many judges you rate.
    You can pause and resume at any time using the same link.
    """)
    st.markdown("---")
    st.markdown("### Section A: Your background")
    st.markdown("""
    **Please select each capacity in which you have practised EU law in areas which
    rely at least to some extent on economic reasoning (e.g. competition or financial law),
    and indicate for how long you have done so.**
    You may choose more than one capacity, in which case please provide the total number of
    years for all capacities combined.
    """)

    selected_caps = st.multiselect(
        "Capacity/capacities in which you have practised:",
        options=CAPACITIES,
        key="bg_capacities",
    )
    years = st.number_input(
        "Total years of practice in the above capacity/capacities:",
        min_value=0, max_value=60, step=1, key="bg_years",
    )

    if st.button("Continue →", type="primary"):
        if not selected_caps:
            st.error("Please select at least one capacity.")
        elif years == 0:
            st.error("Please enter the number of years of practice.")
        else:
            sb.table("respondent_background").insert({
                "respondent_id": rid,
                "capacities": selected_caps,
                "years_experience": int(years),
            }).execute()
            st.session_state.stage = "judge_selection"
            st.rerun()

# ── STAGE 2: Judge selection ────────────────────────────────────────────────────
elif st.session_state.stage == "judge_selection":
    st.markdown("### Section B: Select judges")
    st.markdown("""
    Below is the full list of General Court judges covered by this survey.

    **Please select all judges with whom you have some degree of familiarity**
    (whether through court appearances, indirect knowledge of their judgments,
    academic contact, or any other source). You will then be asked to answer
    questions only for the judges you select here.

    You do not need to have appeared before a judge to rate them — indirect
    familiarity (e.g. through reading their judgments) is sufficient.
    """)

    # Display as sorted alphabetical multiselect
    selected = st.multiselect(
        "Select judges you are familiar with:",
        options=sorted(JUDGES),
        key="judge_select",
        placeholder="Start typing a name or scroll to find judges...",
    )

    st.caption(f"{len(selected)} judge(s) selected")

    if st.button("Continue →", type="primary"):
        if not selected:
            st.error("Please select at least one judge to continue.")
        else:
            # Save selections
            rows = [{"respondent_id": rid, "judge_name": j} for j in selected]
            sb.table("judge_selections").insert(rows).execute()
            st.session_state.selected_judges = selected
            st.session_state.current_judge_idx = 0
            st.session_state.stage = "questions"
            st.rerun()

# ── STAGE 3 & 4: Familiarity + Questions (per judge) ──────────────────────────
elif st.session_state.stage == "questions":
    judges = st.session_state.get("selected_judges", get_judge_selections(rid))
    if not judges:
        st.session_state.stage = "judge_selection"
        st.rerun()

    idx = st.session_state.get("current_judge_idx", 0)
    if idx >= len(judges):
        st.session_state.stage = "done"
        # Mark survey complete
        sb.table("respondents").update(
            {"survey_completed_at": now_utc()}
        ).eq("id", rid).execute()
        st.rerun()

    judge = judges[idx]
    total = len(judges)

    # Progress bar
    completed_so_far = sum(
        1 for j in judges[:idx]
        if len(get_responses_for_judge(rid, j)) == 12
    )
    st.progress((idx) / total, text=f"Judge {idx + 1} of {total}: **{judge}**")
    st.markdown(f"### {judge}")
    st.markdown("---")

    # ── Familiarity source (sub-stage) ─────────────────────────────────────────
    fam_data = get_familiarity(rid, judge)
    existing_responses = get_responses_for_judge(rid, judge)

    if not fam_data:
        st.markdown("**What is the source of your familiarity with this judge?**")
        st.markdown("*You may choose more than one answer.*")

        fam_sources = st.multiselect(
            "Source(s) of familiarity:",
            options=FAMILIARITY_SOURCES,
            key=f"fam_sources_{judge}",
        )
        fam_other = st.text_input(
            "If your familiarity comes from a different context, please specify:",
            key=f"fam_other_{judge}",
            placeholder="Optional",
        )

        if st.button("Continue to questions →", key=f"fam_submit_{judge}", type="primary"):
            if not fam_sources and not fam_other:
                st.error("Please select at least one source of familiarity.")
            else:
                sb.table("judge_familiarity").upsert({
                    "respondent_id": rid,
                    "judge_name": judge,
                    "familiarity_sources": fam_sources,
                    "familiarity_other": fam_other or None,
                }, on_conflict="respondent_id,judge_name").execute()
                st.rerun()

    else:
        # ── Questions Q1-Q12 ────────────────────────────────────────────────────
        st.markdown(ECONOMIC_REASONING_PREAMBLE)
        st.markdown("---")

        answers = {}
        all_answered = True

        def prev_numeric(q):
            r = existing_responses.get(q)
            return int(r["answer_numeric"]) if r and r.get("answer_numeric") else None

        def prev_text(q):
            r = existing_responses.get(q)
            return r["answer_text"] if r and r.get("answer_text") else None

        # Q1
        st.markdown("**Q1.** On a scale from 1 (hardly familiar) to 10 (very familiar), "
                    "how familiar are you with this judge?")
        q1 = st.select_slider("Q1 – Familiarity", options=list(range(1, 11)),
                               value=prev_numeric(1) or 5, key=f"q1_{judge}",
                               label_visibility="collapsed")
        answers[1] = ("numeric", q1)

        st.markdown("---")
        # Q2
        st.markdown("**Q2.** On a scale from 1 (poor) to 10 (excellent), how would you rate "
                    "the knowledge of economics (understanding of economic concepts) of this judge?")
        q2 = st.select_slider("Q2", options=list(range(1, 11)),
                               value=prev_numeric(2) or 5, key=f"q2_{judge}",
                               label_visibility="collapsed")
        answers[2] = ("numeric", q2)

        st.markdown("---")
        # Q3
        st.markdown("**Q3.** On a scale from 1 (no use) to 10 (extensive use), to what extent "
                    "does this judge use economic reasoning to support their decision-making?")
        q3 = st.select_slider("Q3", options=list(range(1, 11)),
                               value=prev_numeric(3) or 5, key=f"q3_{judge}",
                               label_visibility="collapsed")
        answers[3] = ("numeric", q3)

        st.markdown("---")
        # Q4
        st.markdown("**Q4.** Do you consider that the use of economic reasoning by this judge "
                    "has decreased, remained constant, or increased over time?")
        q4_opts = ["", "Decreased", "Remained constant", "Increased"]
        q4_default = prev_text(4) or ""
        q4 = st.selectbox("Q4", options=q4_opts,
                           index=q4_opts.index(q4_default) if q4_default in q4_opts else 0,
                           key=f"q4_{judge}", label_visibility="collapsed")
        if not q4:
            all_answered = False
        answers[4] = ("text", q4)

        st.markdown("---")
        # Q5
        st.markdown("**Q5.** On a scale from 1 (never acknowledges them) through 5 (neutral) "
                    "to 10 (consistently engages with and relies on them), to what extent does "
                    "this judge respond positively to parties' arguments based on economic reasoning?")
        q5 = st.select_slider("Q5", options=list(range(1, 11)),
                               value=prev_numeric(5) or 5, key=f"q5_{judge}",
                               label_visibility="collapsed")
        answers[5] = ("numeric", q5)

        st.markdown("---")
        # Q6
        st.markdown("**Q6.** On a scale from 1 to 10, do you think this judge would consider "
                    "that market regulators and supervisors contribute in a very negative (1), "
                    "neutral (5), or a very positive (10) way to the stability and efficiency "
                    "of the EU economy?")
        q6 = st.select_slider("Q6", options=list(range(1, 11)),
                               value=prev_numeric(6) or 5, key=f"q6_{judge}",
                               label_visibility="collapsed")
        answers[6] = ("numeric", q6)

        st.markdown("---")
        # Q7
        st.markdown("**Q7.** On a scale from 1 (very critical about further EU integration) "
                    "to 10 (very positive about further EU integration), what are this judge's "
                    "views about EU integration understood as allocation of competences between "
                    "Member States and EU bodies?")
        q7 = st.select_slider("Q7", options=list(range(1, 11)),
                               value=prev_numeric(7) or 5, key=f"q7_{judge}",
                               label_visibility="collapsed")
        answers[7] = ("numeric", q7)

        st.markdown("---")
        # Q8
        st.markdown("**Q8.** *\"Just because some rules (laws, regulations) are good for "
                    "business does not mean they are necessarily good for fostering competitive "
                    "markets.\"* On a scale from 1 (strongly disagree) to 10 (strongly agree), "
                    "would this judge agree with the above statement?")
        q8 = st.select_slider("Q8", options=list(range(1, 11)),
                               value=prev_numeric(8) or 5, key=f"q8_{judge}",
                               label_visibility="collapsed")
        answers[8] = ("numeric", q8)

        st.markdown("---")
        # Q9
        st.markdown("**Q9.** *\"Regulations (laws) are necessary for the stability and "
                    "efficient functioning of the economy.\"* On a scale from 1 (strongly "
                    "disagree) to 10 (strongly agree), would this judge agree with the above "
                    "statement?")
        q9 = st.select_slider("Q9", options=list(range(1, 11)),
                               value=prev_numeric(9) or 5, key=f"q9_{judge}",
                               label_visibility="collapsed")
        answers[9] = ("numeric", q9)

        st.markdown("---")
        # Q10
        st.markdown("**Q10.** *\"The economy is mostly self-stabilising and government "
                    "intervention is rarely required as the markets reach efficient outcomes "
                    "on their own and the economy tends towards equilibrium.\"* On a scale "
                    "from 1 (strongly disagree) to 10 (strongly agree), would this judge "
                    "agree with the above statement?")
        q10 = st.select_slider("Q10", options=list(range(1, 11)),
                                value=prev_numeric(10) or 5, key=f"q10_{judge}",
                                label_visibility="collapsed")
        answers[10] = ("numeric", q10)

        st.markdown("---")
        # Q11
        st.markdown("**Q11.** To your knowledge, does this judge have at least some formal "
                    "training in economics (can be a formal degree but also through attending "
                    "courses or workshops, etc.)?")
        q11_opts = ["", "Yes", "No", "Do not know"]
        q11_default = prev_text(11) or ""
        q11 = st.selectbox("Q11", options=q11_opts,
                            index=q11_opts.index(q11_default) if q11_default in q11_opts else 0,
                            key=f"q11_{judge}", label_visibility="collapsed")
        if not q11:
            all_answered = False
        answers[11] = ("text", q11)

        st.markdown("---")
        # Q12
        st.markdown("**Q12.** On a scale from 1 (not confident) to 10 (very confident), "
                    "how confident are you about the information you have provided on this judge?")
        q12 = st.select_slider("Q12", options=list(range(1, 11)),
                                value=prev_numeric(12) or 5, key=f"q12_{judge}",
                                label_visibility="collapsed")
        answers[12] = ("numeric", q12)

        st.markdown("---")

        # Navigation buttons
        col1, col2 = st.columns([1, 2])
        with col1:
            if idx > 0:
                if st.button("← Previous judge"):
                    st.session_state.current_judge_idx = idx - 1
                    st.rerun()

        with col2:
            is_last = (idx == total - 1)
            btn_label = "Submit & Finish ✓" if is_last else "Save & Next judge →"

            if st.button(btn_label, type="primary"):
                if not all_answered:
                    st.error("Please answer Q4 and Q11 before continuing.")
                else:
                    # Save all answers
                    for q_num, (a_type, a_val) in answers.items():
                        if a_type == "numeric":
                            upsert_response(rid, judge, q_num, answer_numeric=int(a_val))
                        else:
                            upsert_response(rid, judge, q_num, answer_text=a_val)

                    # Move to next judge
                    st.session_state.current_judge_idx = idx + 1
                    st.rerun()

# ── STAGE: Done ────────────────────────────────────────────────────────────────
elif st.session_state.stage == "done":
    st.balloons()
    st.success("✅ Survey completed! Thank you for your contribution.")
    st.markdown(f"""
    ### Thank you, {first_name}!

    Your responses have been saved and will contribute to the research on the use
    of economic reasoning by General Court judges.

    **What happens next:**
    - Your responses are stored securely and will be analysed as part of a PhD
      dissertation at KU Leuven (Faculty of Law).
    - Results will be published in aggregated, anonymised form.
    - If you have any questions, please contact the researcher.

    You may close this window.
    """)
