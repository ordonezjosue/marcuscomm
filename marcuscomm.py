import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Marcus Commission KPI Checker", layout="wide")
st.title("📊 Marcus KPI Evaluation Tool")
st.markdown("Upload your monthly sales CSV to automatically evaluate key performance metrics for Marcus.")

# --- Upload CSV ---
uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

# --- Thresholds ---
thresh_gp = 40000
thresh_vmp = 55  # This is "VZ Perks Rate"
thresh_gp_per_smt = 460

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]

        # Clean and filter for Marcus
        df['Employee Full Name'] = df['Employee Full Name'].astype(str).fillna('')
        marcus_df = df[df['Employee Full Name'].str.lower().str.contains("marcus")].copy()

        if marcus_df.empty:
            st.warning("No records found for Marcus. Please check the CSV file.")
        else:
            marcus_df['GP'] = pd.to_numeric(marcus_df['GP'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ Perks Rate'] = pd.to_numeric(marcus_df['VZ Perks Rate'].astype(str).str.replace('%', ''), errors='coerce')
            marcus_df['GP Per SMT'] = pd.to_numeric(marcus_df['GP Per SMT'], errors='coerce')

            marcus = marcus_df.iloc[-1]  # Get latest entry for Marcus

            st.subheader("📋 Evaluation Summary for Marcus")

            # Manual input for VHI/FIOS
            vhi_fios_met = st.selectbox("Did Marcus meet the VHI/FIOS Activations target?", ["Yes", "No"])

            summary_data = {
                "Metric": [
                    "Gross Profit",
                    "VMP (VZ Perks Rate)",
                    "Gross Profit Per Smartphone",
                    "VHI/FIOS Activations"
                ],
                "Value": [
                    f"${marcus['GP']:,.2f}" if not pd.isna(marcus['GP']) else "N/A",
                    f"{marcus['VZ Perks Rate']:.2f}%" if not pd.isna(marcus['VZ Perks Rate']) else "N/A",
                    f"${marcus['GP Per SMT']:,.2f}" if not pd.isna(marcus['GP Per SMT']) else "N/A",
                    vhi_fios_met
                ],
                "Threshold": [
                    f">= ${thresh_gp:,}",
                    f">= {thresh_vmp}%",
                    f">= ${thresh_gp_per_smt}",
                    "Manual Input"
                ],
                "Met?": [
                    "Yes" if not pd.isna(marcus['GP']) and marcus['GP'] >= thresh_gp else "No",
                    "Yes" if not pd.isna(marcus['VZ Perks Rate']) and marcus['VZ Perks Rate'] >= thresh_vmp else "No",
                    "Yes" if not pd.isna(marcus['GP Per SMT']) and marcus['GP Per SMT'] >= thresh_gp_per_smt else "No",
                    vhi_fios_met
                ]
            }

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
