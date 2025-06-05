import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

st.set_page_config(layout="wide")
st.title("\ud83d\udcca Novak's TriNetX Journal-Style Table Generator")

uploaded_file = st.file_uploader("\ud83d\udcc2 Upload your TriNetX CSV file and turn it into a journal-ready table that you can copy and paste into a Word doc or poster. Made by Dr. Daniel Novak at UC Riverside School of Medicine, 2025.", type="csv")
if not uploaded_file:
    st.stop()

# Load and clean CSV
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)
df_trimmed = df_data.copy()

# UI Controls
with st.sidebar.expander("\ud83d\udee0\ufe0f Table Formatting Settings"):
    font_size = st.slider("Font Size", 6, 36, 12)
    h_align = st.selectbox("Text Horizontal Alignment", ["left", "center", "right"])
    v_align = st.selectbox("Text Vertical Alignment", ["top", "middle", "bottom"])
    journal_style = st.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])
    decimal_places = st.slider("Round numerical values to", 0, 5, 2)

add_column_grouping = st.sidebar.checkbox("\ud83d\udccc Add Before/After PSM Column Separators (with headers)")
st.session_state["add_column_grouping"] = add_column_grouping

# Example selected groups for rendering group rows in the table
selected_groups = ["Demographics", "Conditions", "Lab Values", "Medications"]
st.session_state["selected_groups"] = selected_groups

def get_journal_css(journal_style, font_size, h_align, v_align):
    return f"""
    <style>
    table {{
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: {font_size}pt;
    }}
    th, td {{
        border: 1px solid black;
        padding: 6px;
        text-align: {h_align};
        vertical-align: {v_align};
    }}
    th {{
        background-color: #f2f2f2;
        font-weight: bold;
    }}
    .group-row td {{
        background-color: #e6e6e6;
        font-weight: bold;
        text-align: left;
    }}
    </style>
    """

def generate_html_table(df, journal_style, font_size, h_align, v_align):
    try:
        css = get_journal_css(journal_style, font_size, h_align, v_align)
        html = css + "<table>"

        if 'add_column_grouping' in st.session_state and st.session_state['add_column_grouping'] and isinstance(df.columns, pd.MultiIndex):
            group_levels = df.columns.get_level_values(0)
            col_spans = []
            last = None
            span = 0
            for grp in group_levels:
                if grp == last:
                    span += 1
                else:
                    if last is not None:
                        col_spans.append((last, span))
                    last = grp
                    span = 1
            col_spans.append((last, span))

            group_row = "<tr>"
            for grp, span in col_spans:
                group_row += f"<th colspan='{span}'>{grp}</th>"
                if grp in ["Before Propensity Score Matching", "After Propensity Score Matching"]:
                    group_row += "<th style='border: none; background: white; width: 5px'></th>"
            group_row += "</tr>"
            html += group_row

            subheader_row = "<tr>"
            for col in df.columns:
                subheader_row += f"<th>{col[1]}</th>"
                if col[1] in ["Cohort 1 Before: SD", "Before: Standardized Mean Difference", "Cohort 2 After: Patient Count"]:
                    subheader_row += "<th style='border: none; background: white; width: 5px'></th>"
            subheader_row += "</tr>"
            html += subheader_row

        else:
            html += "<tr>"
            for col in df.columns:
                html += f"<th>{col}</th>"
                if col in ["Cohort 1 Before: SD", "Before: Standardized Mean Difference", "Cohort 2 After: Patient Count"]:
                    html += "<th style='border: none; background: white; width: 5px'></th>"
            html += "</tr>"

        selected_groups = st.session_state.get("selected_groups", [])
        for _, row in df.iterrows():
            col_key = ('', 'Characteristic Name') if isinstance(df.columns, pd.MultiIndex) else 'Characteristic Name'
            char_name = str(row.get(col_key, '')).strip().lower()
            if char_name in [label.strip().lower() for label in selected_groups]:
                html += f"<tr class='group-row'><td colspan='{len(df.columns)}'>{row.get(col_key, '')}</td></tr>"
            else:
                html += "<tr>"
                if isinstance(df.columns, pd.MultiIndex):
                    for col in df.columns:
                        html += f"<td>{row[col]}</td>"
                        if col[1] in ["Cohort 1 Before: SD", "Before: Standardized Mean Difference", "Cohort 2 After: Patient Count"]:
                            html += "<td style='border: none; background: white; width: 5px'></td>"
                else:
                    for col in df.columns:
                        html += f"<td>{row[col]}</td>"
                        if col in ["Cohort 1 Before: SD", "Before: Standardized Mean Difference", "Cohort 2 After: Patient Count"]:
                            html += "<td style='border: none; background: white; width: 5px'></td>"
                html += "</tr>"

        html += "</table>"
        return html
    except Exception as e:
        st.error(f"Error generating HTML table: {e}")
        return ""

html_table = generate_html_table(df_trimmed, journal_style, font_size, h_align, v_align)
st.markdown("### \ud83d\udcbe Formatted Table Preview")
st.markdown(html_table, unsafe_allow_html=True)
