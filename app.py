import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import io

# إعدادات الصفحة والواجهة
st.set_page_config(page_title="Test-1 Laboratory", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# قائمة الجنسيات المدعومة
NATIONALITIES = ["", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines", "Nepal"]

# --- نافذة الاستعلام المتقدم (الربط برقم البطاقة) ---
@st.dialog("Company Details Inquiry")
def show_company_inquiry(card_no):
    st.warning("🔄 Background search in progress for Card: " + card_no)
    st.info("Please wait... This may take a few seconds.")
    # (هنا يوضع كود السكرابر الخاص بـ inquiry.mohre.gov.ae كما تم شرحه سابقاً)
    # تظهر النتيجة هنا في مربع حوار يمكن إغلاقه بـ X

# --- وظيفة البحث الأساسية ---
def scrape_data(p, n, d):
    # إعداد المتصفح المخفي
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(p)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        # كتابة الجنسية واختيارها
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(n)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")[0].click()
        # إدخال التاريخ
        driver.execute_script(f"arguments[0].value = '{d}';", driver.find_element(By.ID, "txtBirthDate"))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)
        
        def fetch_val(label):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following::span[1]").text.strip()
            except: return "N/A"

        return {
            "Passport Number": p,
            "Nationality": n,
            "Date of Birth": d,
            "Card Number": fetch_val("Card Number"),
            "Job Description": fetch_val("Job Description"),
            "Basic Salary": fetch_val("Basic Salary"),
            "Total Salary": fetch_val("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة التبويبات ---
tab1, tab2 = st.tabs(["Single Search", "Batch Preview"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    
    # حقول إدخال فارغة تماماً بناءً على طلبك
    passport = col1.text_input("Passport Number", value="")
    nationality = col2.selectbox("Nationality", options=NATIONALITIES, index=0)
    # حل مشكلة التاريخ بجعله نصياً أو اختيارياً
    dob = col3.date_input("Date of Birth", value=None, format="DD/MM/YYYY")

    if st.button("Start Search"):
        if not passport or not nationality or not dob:
            st.error("Please fill all fields first.")
        else:
            start_time = time.time()
            with st.spinner("Searching..."):
                result = scrape_data(passport, nationality, dob.strftime("%d/%m/%Y"))
                if result:
                    end_time = time.time()
                    # إظهار العداد والوقت
                    st.success(f"Success: 1 | Live Timer: {round(end_time - start_time, 2)}s")
                    st.table(pd.DataFrame([result]))
                    
                    # ربط رقم البطاقة بنافذة الاستعلام الجديدة
                    if result["Card Number"] != "N/A":
                        if st.button(f"🔎 Click to query details for Card: {result['Card Number']}"):
                            show_company_inquiry(result["Card Number"])
                else:
                    st.error("No records found.")

with tab2:
    st.subheader("Batch Processing & File Preview")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        # حل مشكلة الصفحة الفاضية بعرض المعاينة فوراً
        df = pd.read_excel(uploaded_file)
        st.write("### File Content Preview")
        st.dataframe(df, use_container_width=True)
        
        if st.button("Start Batch Processing"):
            results_list = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, row in df.iterrows():
                p_no = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', '')).strip()
                b_date = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                
                status_text.text(f"Scanning {i+1}/{len(df)}: {p_no}")
                data = scrape_data(p_no, nat, b_date)
                if data: results_list.append(data)
                progress_bar.progress((i + 1) / len(df))
            
            if results_list:
                st.success(f"Batch completed! {len(results_list)} records found.") #
                final_df = pd.DataFrame(results_list)
                st.table(final_df)
                st.download_button("Download Results CSV", final_df.to_csv(index=False), "results.csv")
    else:
        st.info("Upload your file to start batch processing.") #
