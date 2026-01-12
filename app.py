import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# إعدادات الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    try:
        # هذه الطريقة هي الأنجح على Streamlit Cloud
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Driver Error: {str(e)}")
        return None

def perform_scraping(p, n, d):
    p_str = str(p).strip()
    if not p_str or n == "Select Nationality" or " " in p_str:
        return "Format Error"

    driver = get_driver()
    if not driver: return "Driver Failed"

    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        
        # إدخال البيانات
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p_str)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(n))
        time.sleep(2)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: 
            items[0].click()
        else: 
            return "Not Found"
        
        # تجاوز حماية تاريخ الميلاد
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(d))
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        # استخراج البيانات
        def gv(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span | //*[contains(text(), '{label}')]/parent::div/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else "Not Found"
            except: return "Not Found"

        job = gv("Job Description")
        if job == "Not Found" or job == "": return "Not Found"

        return {
            "Job Description": job, "Card Number": gv("Card Number"),
            "Contract Start": gv("Contract Start"), "Contract End": gv("Contract End"),
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary")
        }
    except: return "Not Found"
    finally:
        if driver: driver.quit()

# الواجهة التي نجحت معك
st.title("HAMADA TRACING SITE TEST")

tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_val = c1.text_input("Passport Number", key="p_single")
    n_val = c2.selectbox("Nationality", ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines"], key="n_single")
    d_val = c3.text_input("Date of Birth (DD/MM/YYYY)", key="d_single")
    
    if st.button("Start Search", key="btn_single"):
        with st.spinner("Searching..."):
            res = perform_scraping(p_val, n_val, d_val)
            if isinstance(res, dict):
                st.success("Success!")
                out_df = pd.DataFrame([res])
                out_df.insert(0, "Passport", p_val)
                out_df.insert(1, "Nationality", n_val)
                out_df.insert(2, "DOB", d_val)
                st.table(out_df)
            else:
                st.error(f"Result: {res}")

with tab2:
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        if st.button("🚀 Start Batch Process"):
            results = []
            for i, row in df.iterrows():
                res = perform_scraping(row[0], row[1], row[2])
                entry = {"Passport": row[0], "Nationality": row[1], "DOB": row[2]}
                if isinstance(res, dict): entry.update(res)
                else: entry["Status"] = res
                results.append(entry)
            st.dataframe(pd.DataFrame(results))
