import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")

# --- دالة تشغيل المتصفح (المحرك) ---
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # هذا السطر مهم جداً للعمل على السيرفر
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Driver Error: {str(e)}")
        return None

def perform_scraping(passport, nationality, dob):
    p_str = str(passport).strip()
    if not p_str or nationality == "Select Nationality" or not str(dob).strip():
        return "Format Error"

    driver = get_driver()
    if not driver: return "Driver Failed" # إذا فشل المتصفح في العمل

    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4) # زيادة وقت الانتظار لضمان تحميل الصفحة
        
        # إدخال البيانات
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p_str)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(2)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: 
            items[0].click()
        else: 
            return "Nationality Error"
        
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(dob))
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8) # الموقع بطيء، نحتاج وقت للتحميل

        # جلب النتائج
        def gv(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span | //*[contains(text(), '{label}')]/parent::div/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else "Not Found"
            except: return "Not Found"

        job = gv("Job Description")
        if job == "Not Found": return "Not Found"

        return {
            "Job Description": job, "Card Number": gv("Card Number"),
            "Contract Start": gv("Contract Start"), "Contract End": gv("Contract End"),
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary")
        }
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if driver: driver.quit()

# --- واجهة المستخدم ---
st.title("HAMADA TRACING SITE TEST")

p_in = st.text_input("Passport Number")
n_in = st.text_input("Nationality (Write exactly as it appears in portal)")
d_in = st.text_input("DOB (DD/MM/YYYY)")

if st.button("Search"):
    with st.spinner("Wait... Running Browser on Server..."):
        res = perform_scraping(p_in, n_in, d_in)
        if isinstance(res, dict):
            st.table(pd.DataFrame([res]))
        else:
            st.error(f"Result: {res}")
