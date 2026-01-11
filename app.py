import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import io

# Page Config
st.set_page_config(page_title="Test-1 Laboratory", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# Authentication
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    with st.form("login_gate"):
        st.subheader("Protected Access")
        pwd = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish":
                st.session_state['auth'] = True
                st.rerun()
            else: st.error("Access Denied")
    st.stop()

# --- Inquiry Dialog (Second Step) ---
@st.dialog("Work Permit Details")
def show_company_details(card_number):
    st.info(f"⏳ Please wait... Fetching data for Card No: {card_number}")
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options, use_subprocess=False)
        driver.get("https://inquiry.mohre.gov.ae/")
        
        select = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlService")))
        select.click()
        driver.find_element(By.XPATH, "//option[contains(text(), 'Electronic Work Permit Information')]").click()
        
        driver.find_element(By.ID, "txtTransactionNo").send_keys(card_number)
        captcha_img = driver.find_element(By.ID, "imgCaptcha")
        st.image(captcha_img.screenshot_as_png, caption="Verification Code Required")
        
        with st.form("cap_submit"):
            code = st.text_input("Enter Code")
            if st.form_submit_button("Verify & Fetch"):
                driver.find_element(By.ID, "txtCaptcha").send_keys(code)
                driver.find_element(By.ID, "btnSearch").click()
                time.sleep(4)
                
                # Fetching final info
                name = driver.find_element(By.ID, "lblWorkerNameEn").text
                est = driver.find_element(By.ID, "lblEstNameEn").text
                code_est = driver.find_element(By.ID, "lblEstNo").text
                
                st.success("✅ Details Found")
                st.write(f"**Name:** {name}")
                st.write(f"**Establishment:** {est}")
                st.write(f"**Est Code:** {code_est}")
    except: st.error("Connection failed.")
    finally:
        if driver: driver.quit()

# --- Core Scraper Function ---
def scrape_primary(p, n, d):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(n)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")[0].click()
        driver.execute_script(f"arguments[0].value = '{d}';", driver.find_element(By.ID, "txtBirthDate"))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)
        
        def gv(label):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following::span[1]").text.strip()
            except: return "N/A"

        return {"Passport": p, "Card Number": gv("Card Number"), "Job": gv("Job Description"), "Basic": gv("Basic Salary"), "Total": gv("Total Salary")}
    except: return None
    finally: driver.quit()

# --- UI Tabs ---
tab1, tab2 = st.tabs(["Single Person Search", "Batch Preview"])

with tab1:
    st.subheader("Single Person Search") #
    c1, c2, c3 = st.columns(3)
    p_v = c1.text_input("Passport Number")
    n_v = c2.selectbox("Nationality", ["Egypt", "India", "Pakistan", "Bangladesh"])
    d_v = c3.date_input("Date of Birth", format="DD/MM/YYYY") #
    
    if st.button("Search"):
        with st.spinner("Processing..."):
            res = scrape_primary(p_v, n_v, d_v.strftime("%d/%m/%Y"))
            if res:
                st.table(pd.DataFrame([res])) #
                if res["Card Number"] != "N/A":
                    if st.button(f"🔎 Click to Query Details for Card: {res['Card Number']}"):
                        show_company_details(res["Card Number"])
            else: st.error("Record not found.")

with tab2:
    st.subheader("Batch Search & Preview")
    up_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if up_file:
        df_batch = pd.read_excel(up_file)
        st.write("### File Content Preview")
        st.dataframe(df_batch, use_container_width=True) # Now it's not empty
        
        if st.button("Start Batch Processing"):
            results = []
            progress = st.progress(0)
            status = st.empty()
            
            for i, row in df_batch.iterrows():
                pass_no = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                
                status.text(f"Scanning {i+1}/{len(df_batch)}: {pass_no}")
                data = scrape_primary(pass_no, nat, dob)
                if data: results.append(data)
                progress.progress((i + 1) / len(df_batch))
            
            if results:
                st.success(f"Batch completed! {len(results)} records found.")
                res_df = pd.DataFrame(results)
                st.table(res_df)
                st.download_button("Download Results CSV", res_df.to_csv(index=False), "results.csv")
