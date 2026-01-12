import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # تم إزالة أي إضافات تسبب تعارض مع نظام linux على السيرفر
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"خطأ في تشغيل المحرك: {e}")
        return None

# دالة البحث
def search_mohre(p, n, d):
    driver = get_driver()
    if not driver: return "Driver Error"
    
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 15)
        
        # إدخال رقم الجواز
        wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(str(p))
        
        # اختيار الجنسية
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        search_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")))
        search_box.send_keys(str(n))
        
        # نقرة لاختيار الجنسية من القائمة
        item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")))
        item.click()
        
        # إدخال تاريخ الميلاد عبر Script (هذه الطريقة هي التي نجحت معك سابقاً)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_field, str(d))
        
        # الضغط على بحث
        driver.find_element(By.ID, "btnSubmit").click()
        
        # انتظار النتائج
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Job Description')]")))
        
        def gv(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "N/A"

        return {
            "Job": gv("Job Description"),
            "Card": gv("Card Number"),
            "Start": gv("Contract Start"),
            "End": gv("Contract End"),
            "Basic": gv("Basic Salary"),
            "Total": gv("Total Salary")
        }
    except:
        return "Not Found"
    finally:
        driver.quit()

# الواجهة
st.title("HAMADA TRACING SYSTEM")
p_in = st.text_input("Passport")
n_in = st.selectbox("Nationality", ["Egypt", "India", "Pakistan", "Bangladesh"])
d_in = st.text_input("DOB (DD/MM/YYYY)")

if st.button("Search"):
    res = search_mohre(p_in, n_in, d_in)
    if isinstance(res, dict):
        st.success("Success!")
        st.table(pd.DataFrame([res]))
    else:
        st.error(f"Result: {res}")
