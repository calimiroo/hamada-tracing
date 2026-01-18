import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re

# --- 1. Page Config & Professional Styling ---
st.set_page_config(page_title="MOHRE Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdfdfd; }
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        height: 3em;
        border-radius: 5px;
    }
    /* Fixed Table Colors */
    .stDataFrame [data-testid="stTable"] td {
        border: 1px solid #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 HAMADA TRACING SYSTEM")

# --- 2. Session Management ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'batch_data' not in st.session_state:
    st.session_state.batch_data = []

# Full Nationality List
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- 3. Browser Setup (Headless for Cloud) ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    return uc.Chrome(options=options, headless=True, use_subprocess=True)

# --- 4. Coloring Logic ---
def color_rows(row):
    color = '#d4edda' if row['Status'] == 'Found' else '#f8d7da'
    return [f'background-color: {color}'] * len(row)

# --- 5. Extraction Logic ---
def run_search(passport, nationality, dob):
    driver = None
    try:
        driver = get_driver()
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        
        wait = WebDriverWait(driver, 10)
        # Fill Passport
        wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        
        # Nationality Selection
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(0.5)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(0.8)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        # Date of Birth
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob)
        
        # Submit
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(4)
        
        # Extract Results
        try:
            card_no = driver.find_element(By.XPATH, "//span[contains(text(), 'Card Number')]/following::span[1]").text.strip()
            if not card_no: return None
            
            job = driver.find_element(By.XPATH, "//span[contains(text(), 'Job Description')]/following::span[1]").text.strip()
            salary = driver.find_element(By.XPATH, "//span[contains(text(), 'Total Salary')]/following::span[1]").text.strip()
            
            return {
                "Passport": passport, "Nationality": nationality, "DOB": dob,
                "Card Number": card_no, "Job": job, "Salary": salary, "Status": "Found"
            }
        except: return None
    except: return None
    finally:
        if driver: driver.quit()

# --- 6. Security & UI ---
if not st.session_state.authenticated:
    with st.container():
        st.subheader("System Lock")
        pwd = st.text_input("Enter Key", type="password")
        if st.button("Unlock") and pwd == "Bilkish":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# Tabs
t1, t2 = st.tabs(["Single Search", "Batch Processing"])

with t1:
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number")
    n_in = col2.selectbox("Nationality", countries_list)
    d_in = col3.date_input("Date of Birth", value=None, min_value=datetime(1940,1,1))
    
    if st.button("Run Search"):
        if p_in and d_in:
            with st.spinner("Processing..."):
                res = run_search(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res:
                    st.success("Record Found")
                    st.dataframe(pd.DataFrame([res]).style.apply(color_rows, axis=1))
                else:
                    st.error("No Record Found")

with t2:
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file)
        st.info(f"Loaded {len(df_input)} records.")
        
        if st.button("Start Batch Operation"):
            st.session_state.batch_data = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            table_placeholder = st.empty() # Placeholder for live updates
            
            for idx, row in df_input.iterrows():
                p_val = str(row.get('Passport Number', '')).strip()
                n_val = str(row.get('Nationality', '')).strip()
                d_raw = row.get('Date of Birth')
                
                # Dynamic Date Handling
                try:
                    d_val = pd.to_datetime(d_raw).strftime('%d/%m/%Y') if not isinstance(d_raw, str) else d_raw
                except: d_val = str(d_raw)
                
                status_text.write(f"🔍 Searching: {p_val} ({idx+1}/{len(df_input)})")
                
                result = run_search(p_val, n_val, d_val)
                
                if result:
                    st.session_state.batch_data.append(result)
                else:
                    st.session_state.batch_data.append({
                        "Passport": p_val, "Nationality": n_val, "DOB": d_val,
                        "Card Number": "N/A", "Job": "N/A", "Salary": "N/A", "Status": "Not Found"
                    })
                
                # LIVE UPDATE: Update table on every loop
                current_df = pd.DataFrame(st.session_state.batch_data)
                table_placeholder.dataframe(current_df.style.apply(color_rows, axis=1), use_container_width=True)
                
                progress_bar.progress((idx + 1) / len(df_input))
            
            status_text.success("Batch Completed!")
            
            # Final Download
            final_df = pd.DataFrame(st.session_state.batch_data)
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Final Report", csv, "batch_report.csv", "text/csv")
