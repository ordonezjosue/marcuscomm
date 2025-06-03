import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Marcus Commission Calculator", layout="wide")
st.title("📊 Marcus Commission Calculator")

st.markdown("""
Upload your monthly sales CSV to automatically evaluate key performance metrics for Marcus.

### 📂 How to Export Your Sales CSV from Power BI:
1. Log into **Power BI**  
2. Go to **WZ Sales Analysis**  
3. Scroll to the bottom and select **KPI Details**  
4. At the top, click **Employee**  
5. Click the **three dots (⋯)** next to "More Options"  
6. Select **Export data**  
7. Choose **Summarized data**  
8. Select **.CSV** as the file format and save it to your computer  
9. Upload the CSV file below ⬇️
""")

# --- Upload CSV ---
uploaded_file = st.file_uploader("📁 Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    st.success("✅ Power BI sales CSV uploaded successfully!")
    st.markdown("➡️ Now please upload the RQ report (.xlsx) to continue.")

# --- Upload VHI/FIOS Excel File ---
vhi_file = st.file_uploader("📄 Upload the RQ report from Performance Mertrics Summary Report", type=["xlsx"])

# --- Thresholds ---
thresh_gp = 25000
thresh_vmp = 55  # This is "VZ Perks Rate"
thresh_gp_per_smt = 460
thresh_vhi_fios = 8

if uploaded_file is not None and vhi_file is not None:
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
            marcus_df['GP Per SMT'] = pd.to_numeric(marcus_df['GP Per SMT'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')

            marcus = marcus_df.iloc[-1]  # Get latest entry for Marcus

            # --- Load VHI/FIOS Activations ---
            try:
                vhi_df = pd.read_excel(vhi_file, engine='openpyxl')
                vhi_df.columns = [col.encode('ascii', 'ignore').decode().strip().replace('
', ' ').replace('
', '') for col in vhi_df.columns]
                if any(col in vhi_df.columns for col in ['(Q) 5G Consumer Internet', '(Q) FiOS Sales']):
                    vhi_df['Employee Full Name'] = vhi_df['Employee Full Name'].astype(str).fillna('')
                    marcus_vhi = vhi_df[vhi_df['Employee Full Name'].str.lower().str.contains('marcus')]
                    vhi_fios_5g = pd.to_numeric(marcus_vhi['(Q) 5G Consumer Internet'].dropna().sum()) if '(Q) 5G Consumer Internet' in marcus_vhi.columns else 0
                    fios_sales = pd.to_numeric(marcus_vhi['(Q) FiOS Sales'].dropna().sum()) if '(Q) FiOS Sales' in marcus_vhi.columns else 0
                    vhi_fios_count = vhi_fios_5g + fios_sales
                else:
                    st.warning("Required columns '(Q) 5G Consumer Internet' or '(Q) FiOS Sales' not found in Excel file.")
                    vhi_fios_count = 0
            except Exception as e:
                st.warning(f"Could not process Excel file: {e}")
                vhi_fios_count = 0

            st.subheader("📋 Marcus Commission Calculator")

            # KPI Evaluations
            met_gp = not pd.isna(marcus['GP']) and marcus['GP'] >= thresh_gp
            met_vmp = not pd.isna(marcus['VZ Perks Rate']) and marcus['VZ Perks Rate'] >= thresh_vmp
            met_gp_per_smt = not pd.isna(marcus['GP Per SMT']) and marcus['GP Per SMT'] >= thresh_gp_per_smt
            met_vhi_fios = vhi_fios_count >= thresh_vhi_fios

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
                    f"{vhi_fios_count}"
                ],
                "Threshold": [
                    f">= ${thresh_gp:,}",
                    f">= {thresh_vmp}%",
                    f">= ${thresh_gp_per_smt}",
                    f">= {thresh_vhi_fios}"
                ],
                "Met?": [
                    "Yes" if met_gp else "No",
                    "Yes" if met_vmp else "No",
                    "Yes" if met_gp_per_smt else "No",
                    "Yes" if met_vhi_fios else "No"
                ]
            }

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

            # --- Commission Calculator ---
            st.subheader("💰 Commission Calculator")

            all_targets_met = all([met_gp, met_vmp, met_gp_per_smt, met_vhi_fios])
            commission_rate = 0.30 if all_targets_met else 0.25
            commission_earned = marcus['GP'] * commission_rate if not pd.isna(marcus['GP']) else 0

            st.markdown(f"**Commission Rate:** {'30%' if all_targets_met else '25%'}")
            st.markdown(f"**Commission Earned:** ${commission_earned:,.2f}")

    except Exception as e:
        st.error(f"Error processing file: {e}")
