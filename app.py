import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator

# --- Page Config ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")

# --- Security & Session ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'stop' not in st.session_state: st.session_state.stop = False

if not st.session_state.auth:
    st.subheader("Login Required")
    if st.text_input("Password", type="password") == "Hamada":
        if st.button("Login"):
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- Functions ---
def translate_ar_to_en(text):
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='auto', target='en').translate(text)
    except: pass
    return text

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def run_search(passport, nationality, dob):
    driver = get_driver()
    if not driver: return "System Error"
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(passport))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(2)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Nationality Not Found"
        
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(dob))
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)
        
        def gv(lbl):
            try:
                xpath = f"//*[contains(text(), '{lbl}')]/following-sibling::span"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "N/A"

        job = gv("Job Description")
        if job == "N/A": return "No Data Found"

        return {
            "Job": translate_ar_to_en(job),
            "Card": gv("Card Number"),
            "Start": gv("Contract Start"),
            "End": gv("Contract End"),
            "Basic": gv("Basic Salary"),
            "Total": gv("Total Salary")
        }
    except: return "Search Failed"
    finally: driver.quit()

# --- UI ---
st.title("🛡️ HAMADA TRACING SYSTEM")
st.sidebar.button("Log Out", on_click=lambda: st.session_state.update({"auth": False}))

tab1, tab2 = st.tabs(["🔍 Single Search", "📁 Batch Processing"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p = c1.text_input("Passport")
    n = c2.text_input("Nationality") # يمكنك استبدالها بـ Selectbox لاحقاً
    d = c3.text_input("DOB (DD/MM/YYYY)")
    if st.button("Start Search"):
        with st.spinner("Processing..."):
            res = run_search(p, n, d)
            if isinstance(res, dict): st.table(pd.DataFrame([res]))
            else: st.error(res)

with tab2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
    if f:
        df = pd.read_excel(f)
        if st.button("🚀 Start Batch"):
            st.session_state.stop = False
            results = []
            m1, m2, m3 = st.columns(3)
            timer_p, count_p, success_p = m1.empty(), m2.empty(), m3.empty()
            pb = st.progress(0)
            table_spot = st.empty()
            start_time = time.time()
            success_count = 0

            for i, row in df.iterrows():
                if st.session_state.stop: break
                timer_p.metric("⏳ Timer", f"{round(time.time()-start_time, 1)}s")
                count_p.metric("📊 Records", f"{i+1}/{len(df)}")
                success_p.metric("✅ Success", success_count)
                
                data = run_search(row[0], row[1], row[2])
                entry = {"Passport": row[0], "Status": "Success" if isinstance(data, dict) else data}
                if isinstance(data, dict):
                    entry.update(data)
                    success_count += 1
                results.append(entry)
                pb.progress((i+1)/len(df))
                table_spot.dataframe(pd.DataFrame(results))
            
            st.success("Batch Completed!")
            st.download_button("Download CSV", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "Results.csv")
