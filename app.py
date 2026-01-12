import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MOHRE Tracing System", layout="wide")

# --- إدارة الجلسة (Session State) ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'stop' not in st.session_state: st.session_state.stop = False

# --- وظيفة تسجيل الخروج (بديلة لـ Share) ---
def sign_out():
    st.session_state.authenticated = False
    st.rerun()

# --- نظام الدخول ---
if not st.session_state.authenticated:
    st.subheader("🔑 نظام الدخول")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()
else:
    # زر تسجيل الخروج في أعلى الصفحة بدلاً من Share
    st.sidebar.button("🔴 Sign Out / خروج", on_click=sign_out)

# --- محرك البحث السحابي ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        st.error(f"خطأ في المحرك: {e}")
        return None

def scrape_data(p, n, d):
    driver = get_driver()
    if not driver: return "Driver Fail"
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(str(p))
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control").send_keys(str(n))
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        else: return "Nationality Error"
        
        dob_f = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].value = arguments[1];", dob_f, str(d))
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)

        # تحسين قراءة البيانات لضمان دقة النتائج
        def get_val(lbl):
            try:
                # محاولة البحث عن النص في الـ span المجاور للعنوان
                return driver.find_element(By.XPATH, f"//span[contains(text(), '{lbl}')]/following-sibling::span").text.strip()
            except:
                try: # محاولة البحث في الهيكل البديل للموقع
                    return driver.find_element(By.XPATH, f"//div[contains(text(), '{lbl}')]/following-sibling::div").text.strip()
                except: return "N/A"

        job = get_val("Job Description")
        if job == "N/A": return "Not Found"

        return {
            "Job": job, "Card": get_val("Card Number"),
            "Start": get_val("Contract Start"), "End": get_val("Contract End"),
            "Basic": get_val("Basic Salary"), "Total": get_val("Total Salary")
        }
    except: return "Error"
    finally: driver.quit()

# --- الواجهة ---
st.title("🛡️ HAMADA TRACING SYSTEM v4.0")

tab1, tab2 = st.tabs(["🔍 بحث فردي", "📂 معالجة إكسل"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("رقم الجواز")
    n_in = c2.text_input("الجنسية")
    d_in = c3.text_input("تاريخ الميلاد")
    if st.button("بحث"):
        res = scrape_data(p_in, n_in, d_in)
        if isinstance(res, dict): st.success("تم بنجاح"); st.table(pd.DataFrame([res]))
        else: st.error(f"النتيجة: {res}")

with tab2:
    f = st.file_uploader("ارفع ملف الإكسل", type=["xlsx"])
    if f:
        df_in = pd.read_excel(f)
        total_rec = len(df_in)
        
        # خيار إظهار ملف الإكسل المرفوع
        if st.checkbox("إظهار الملف المرفوع"):
            st.write(df_in)

        col1, col2, col3, col4 = st.columns(4)
        if col1.button("▶️ بدء المعالجة"):
            st.session_state.stop = False
            results = []
            
            # --- العدادات والإحصائيات ---
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            timer_p = stat_col1.empty()
            count_p = stat_col2.empty()
            success_p = stat_col3.empty()
            
            progress_bar = st.progress(0)
            table_spot = st.empty()
            
            start_time = time.time()
            success_count = 0

            for i, row in df_in.iterrows():
                if st.session_state.stop: break
                
                # تحديث الوقت والإحصاء
                elapsed = round(time.time() - start_time, 1)
                timer_p.metric("⏳ الوقت المنقضي", f"{elapsed}s")
                count_p.metric("📊 السجلات", f"{i+1} من {total_rec}")
                success_p.metric("✅ النجاح", success_count)
                
                # تنفيذ البحث
                data = scrape_data(row[0], row[1], row[2])
                
                # تجميع النتيجة (لكل الأسماء)
                entry = {"Passport": row[0], "Name": row[1], "Status": "Success" if isinstance(data, dict) else data}
                if isinstance(data, dict):
                    entry.update(data)
                    success_count += 1
                else:
                    # تعبئة القيم بـ "N/A" في حال الفشل لإبقاء الجدول متسقاً
                    for col in ["Job", "Card", "Start", "End", "Basic", "Total"]: entry[col] = "N/A"
                
                results.append(entry)
                progress_bar.progress((i + 1) / total_rec)
                table_spot.dataframe(pd.DataFrame(results))

            st.success("✅ اكتملت المهمة!")
            st.download_button("📥 تحميل النتائج", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "Results.csv")
        
        if col2.button("🛑 إيقاف"):
            st.session_state.stop = True
