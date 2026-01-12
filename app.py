import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")

def get_driver():
    options = Options()
    options.add_argument("--headless=new") # استخدام النسخة الجديدة من headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # محاولة تشغيل المتصفح باستخدام المسارات الافتراضية للسيرفر
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"خطأ في تشغيل المتصفح على السيرفر: {str(e)}")
        return None

def perform_scraping(passport, nationality, dob):
    p_str = str(passport).strip()
    if not p_str or nationality == "Select Nationality" or " " in p_str:
        return "Format Error"

    driver = get_driver()
    if not driver: return "Driver Error"

    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5) # وقت كافٍ للتحميل
        
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
            return "Not Found"
        
        # كتابة التاريخ مباشرة عبر JavaScript لتجنب مشاكل القائمة
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(dob))
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        # استخراج النتائج
        def gv(label):
            try:
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::span"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "Not Found"

        job = gv("Job Description")
        if job == "Not Found" or job == "": return "Not Found"

        return {
            "Job Description": job,
            "Card Number": gv("Card Number"),
            "Contract Start": gv("Contract Start"),
            "Contract End": gv("Contract End"),
            "Basic Salary": gv("Basic Salary"),
            "Total Salary": gv("Total Salary")
        }
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if driver: driver.quit()

# --- واجهة المستخدم ---
st.title("HAMADA TRACING SITE TEST")

tab1, tab2 = st.tabs(["بحث فردي", "بحث بالجملة"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("رقم الجواز")
    n_in = c2.text_input("الجنسية (اكتبها بالإنجليزية كما في الموقع)")
    d_in = c3.text_input("تاريخ الميلاد DD/MM/YYYY")
    
    if st.button("بدء البحث"):
        with st.spinner("جاري تشغيل المتصفح والبحث..."):
            res = perform_scraping(p_in, n_in, d_in)
            if isinstance(res, dict):
                st.success("تم العثور على البيانات!")
                st.table(pd.DataFrame([res]))
            else:
                st.error(f"النتيجة: {res}")

with tab2:
    uploaded_file = st.file_uploader("ارفع ملف الإكسل", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"عدد السجلات: {len(df)}")
        if st.button("بدء المعالجة"):
            results = []
            bar = st.progress(0)
            for i, row in df.iterrows():
                res = perform_scraping(row[0], row[1], row[2])
                entry = {"Passport": row[0], "Result": res}
                if isinstance(res, dict): entry.update(res)
                results.append(entry)
                bar.progress((i + 1) / len(df))
            st.dataframe(pd.DataFrame(results))
