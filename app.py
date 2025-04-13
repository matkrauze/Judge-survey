import streamlit as st
import pandas as pd
import uuid
import os
import seaborn as sns
import matplotlib.pyplot as plt

# Load judges and questions
judges_df = pd.read_csv("unique_judges.csv", header=None)
questions_df = pd.read_csv("Questions - Questions.csv", header=None)

# Prepare lists
judges = judges_df[0].dropna().tolist()
questions = questions_df[0].dropna().astype(str).tolist()
dropdown_options = ["Increased", "Remained constant", "Decreased"]
scale_options = list(range(1, 11))  # 1 to 10 scale

# App layout
st.title("Judge Survey App")
st.markdown("""
#### Please enter the access code to continue:
""")

password = st.text_input("Access Code", type="password")
if password != "secure123":
    st.warning("Please enter the correct access code to proceed.")
    st.stop()

# Survey UI
st.markdown("---")
st.markdown("### Select the judges you would like to review")
selected_judges = st.multiselect("Choose one or more judges", judges)
responses = []
missing_entries = []

if selected_judges:
    st.markdown("---")
    st.markdown(f"### Answering survey for {len(selected_judges)} selected judges")

    for idx, judge in enumerate(selected_judges):
        st.markdown(f"#### {idx + 1} of {len(selected_judges)}: {judge}")
        with st.expander(f"Survey for {judge}", expanded=True):
            for i, question in enumerate(questions):
                q_label = f"Q{i+1}. {question.strip()}"
                key = f"{judge}_q{i}"

                if i == 3:
                    # Q4: dropdown
                    answer = st.selectbox(q_label, options=[""] + dropdown_options, key=key)
                    if answer == "":
                        missing_entries.append((judge, q_label))
                else:
                    # All others: select_slider with no default
                    answer = st.select_slider(q_label, options=[""] + scale_options, key=key)
                    if answer == "":
                        missing_entries.append((judge, q_label))

                responses.append({
                    "responder_id": "",
                    "judge": judge,
                    "question": q_label,
                    "answer": answer
                })

    if st.button("Submit Survey"):
        if missing_entries:
            st.error("Oops! You're missing some responses:")
            for judge, question in missing_entries:
                st.write(f"❌ {judge} → {question}")
            st.warning("Please complete all required questions before submitting.")
        else:
            responder_id = str(uuid.uuid4())
            for r in responses:
                r["responder_id"] = responder_id

            df = pd.DataFrame(responses)
            output_file = "responses.csv"
            if os.path.exists(output_file):
                df.to_csv(output_file, mode='a', header=False, index=False)
            else:
                df.to_csv(output_file, index=False)

            st.success("Survey submitted and saved successfully!")
            st.write("Your responses:")
            st.dataframe(df)

# Optional admin tools
st.markdown("---")
st.markdown("## \U0001F4CA Admin Panel")

if os.path.exists("responses.csv"):
    if st.checkbox("Show all responses"):
        df_all = pd.read_csv("responses.csv")
        st.dataframe(df_all)

        st.download_button("Download All Responses", df_all.to_csv(index=False), "responses.csv")

        if st.checkbox("Show summary statistics"):
            avg_df = df_all[df_all['answer'].apply(lambda x: str(x).isdigit())].copy()
            avg_df['answer'] = avg_df['answer'].astype(int)

            summary_questions = avg_df.groupby("question")["answer"].mean().round(2).reset_index()
            st.write("### Average score per question")
            st.dataframe(summary_questions)

            summary_per_judge_question = avg_df.groupby(["judge", "question"])["answer"].mean().round(2).reset_index()
            st.write("### Average score per question per judge")
            st.dataframe(summary_per_judge_question)

            # Shorten question labels for heatmap safely
            def shorten_label(q):
                q = q.strip()
                if q.lower().startswith("q") and "." in q:
                    prefix, rest = q.split(".", 1)
                    rest = rest.strip()
                    return f"{prefix}. {rest[:30]}{'...' if len(rest) > 30 else ''}"
                return q[:30] + ("..." if len(q) > 30 else "")

            summary_per_judge_question["short_question"] = summary_per_judge_question["question"].apply(shorten_label)
            heatmap_data = summary_per_judge_question.pivot(index="judge", columns="short_question", values="answer")

            st.write("### Heatmap of Scores (Judges x Questions)")
            fig, ax = plt.subplots(figsize=(12, len(heatmap_data) * 0.6))
            sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="YlGnBu", cbar=True, ax=ax)
            st.pyplot(fig)
else:
    st.info("No survey responses have been submitted yet.")
