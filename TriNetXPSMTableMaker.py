import streamlit as st
import pandas as pd

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
