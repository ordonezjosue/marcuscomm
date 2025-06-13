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

# --- Thresholds ---
thresh_gp = 25000
thresh_vmp = 55
thresh_gp_per_smt = 460
thresh_vhi_fios = 8

if uploaded_file is not None:
    try:
        st.success("✅ Power BI sales CSV uploaded successfully!")

        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]

        df['Employee Full Name'] = df['Employee Full Name'].astype(str).fillna('')
        marcus_df = df[df['Employee Full Name'].str.lower().str.contains("marcus")].copy()

        if marcus_df.empty:
            st.warning("No records found for Marcus. Please check the CSV file.")
        else:
            # Clean numeric fields
            marcus_df['GP'] = pd.to_numeric(marcus_df['GP'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ Perks Rate'] = pd.to_numeric(marcus_df['VZ Perks Rate'].astype(str).str.replace('%', ''), errors='coerce')
            marcus_df['GP Per SMT'] = pd.to_numeric(marcus_df['GP Per SMT'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            marcus_df['VZ FWA GA'] = pd.to_numeric(marcus_df['VZ FWA GA'], errors='coerce')
            marcus_df['VZ FIOS GA'] = pd.to_numeric(marcus_df['VZ FIOS GA'], errors='coerce')

            marcus = marcus_df.iloc[-1]  # Latest entry

            # KPI Evaluations
            met_gp = not pd.isna(marcus['GP']) and marcus['GP'] >= thresh_gp
            met_vmp = not pd.isna(marcus['VZ Perks Rate']) and marcus['VZ Perks Rate'] >= thresh_vmp
            met_gp_per_smt = not pd.isna(marcus['GP Per SMT']) and marcus['GP Per SMT'] >= thresh_gp_per_smt

            vhi_fios_count = 0
            if not pd.isna(marcus['VZ FWA GA']):
                vhi_fios_count += marcus['VZ FWA GA']
            if not pd.isna(marcus['VZ FIOS GA']):
                vhi_fios_count += marcus['VZ FIOS GA']

            met_vhi_fios = vhi_fios_count >= thresh_vhi_fios

            # Summary Table
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
                    f"{int(vhi_fios_count)}"
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
            st.subheader("📋 Marcus Performance Summary")
            st.dataframe(summary_df, use_container_width=True)

            # --- Commission Calculator ---
            st.subheader("💰 Commission Calculator")
            all_targets_met = all([met_gp, met_vmp, met_gp_per_smt, met_vhi_fios])
            commission_rate = 0.30 if all_targets_met else 0.25
            commission_earned = marcus['GP'] * commission_rate if not pd.isna(marcus['GP']) else 0

            st.markdown(f"**Commission Rate:** {'30%' if all_targets_met else '25%'}")
            st.markdown(f"**Commission Earned:** ${commission_earned:,.2f}")

            # --- Explanation of Pay Structure ---
            st.markdown("---")
            st.subheader("📘 Commission Structure Explained")
            st.markdown("""
Your commission is based on whether you meet or exceed **four key performance thresholds** for the month:

1. **Gross Profit (GP)** must be at least **$25,000**
2. **VZ Perks Rate (VMP)** must be **55% or higher**
3. **Gross Profit Per Smartphone (GP/SMT)** must be **$460 or more**
4. **VHI/FIOS Activations** (combined total of VZ FWA GA and VZ FIOS GA) must be **8 or more** (For FIOS, only transactions that were successfully installed will be counted. For VHI, only transactions that were activated will be counted, minus VHI cancelled within 30 days)

### 💸 Commission Payout Logic:
- If **all 4 metrics are met**, your commission rate is **30% of your total GP**
- If **any metric is missed**, your commission rate is **25% of your total GP**

This calculator automatically checks each of those for you and gives you your final **commission rate** and **earnings** based on your performance.

If you have any questions, reach out to management or your team lead.
""")

    except Exception as e:
        st.error(f"Error processing file: {e}")
