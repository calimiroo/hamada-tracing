import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # محاولة تشغيل المتصفح من المسار الافتراضي للنظام
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def run_search(passport, nationality, dob):
    driver = get_driver()
    if not driver: return "System Error"
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        
        # إدخال البيانات
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(passport))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(nationality))
        time.sleep(2)
        
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Not Found"
        
        # حقن التاريخ (الطريقة الناجحة في صورتك الأولى)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_field, str(dob))
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)
        
        # جلب النتيجة
        res_text = driver.page_source
        if "Job Description" in res_text:
            def gv(label):
                try:
                    xpath = f"//*[contains(text(), '{label}')]/following-sibling::span"
                    return driver.find_element(By.XPATH, xpath).text.strip()
                except: return "N/A"
            
            return {
                "Job": gv("Job Description"), "Card": gv("Card Number"),
                "Start": gv("Contract Start"), "End": gv("Contract End"),
                "Salary": gv("Total Salary")
            }
        return "Not Found"
    except: return "Search Failed"
    finally:
        driver.quit()

# --- الواجهة ---
st.title("HAMADA TRACING SYSTEM")
c1, c2, c3 = st.columns(3)
p = c1.text_input("Passport")
n = c2.selectbox("Nationality", ["Egypt", "India", "Pakistan", "Bangladesh"])
d = c3.text_input("DOB (DD/MM/YYYY)")

if st.button("Start Search"):
    with st.spinner("Processing..."):
        result = run_search(p, n, d)
        if isinstance(result, dict):
            st.success("Success!")
            st.table(pd.DataFrame([result]))
        else:
            st.error(f"Result: {result}")
