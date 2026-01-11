import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# إعداد الصفحة
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# قاموس ترجمة شامل (يمكنك إضافة أي مهنة جديدة هنا)
job_translation = {
    "مدير المنطقة": "Area Manager",
    "عامل": "Worker",
    "مهندس": "Engineer",
    "محاسب": "Accountant",
    "سائق": "Driver",
    "مندوب مبيعات": "Sales Representative",
    "فني": "Technician",
    "محصل ديون": "Debt Collector",
    "بائع": "Salesman",
    "مدير": "Manager"
}

# قائمة الجنسيات
countries_list = ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Jordan", "Syria"] # تم الاختصار للتوضيح

# دالة الاستخراج
def extract_data(passport, nationality, dob_str):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, use_subprocess=False)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        
        # إدخال البيانات (المنطق الخاص بك)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        # ... تكملة خطوات البحث ...
        
        # محاكاة استخراج القيمة (استبدلها بمنطق get_value الخاص بك)
        job_ar = "مدير المنطقة" # مثال للقيمة المستخرجة
        card_num = "124119312"
        
        # تطبيق الترجمة فوراً
        translated_job = job_translation.get(job_ar.strip(), job_ar)

        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": translated_job, # المهنة المترجمة
            "Card Number": card_num,
            "Basic Salary": "8000",
            "Total Salary": "16000"
        }
    except:
        return None
    finally:
        driver.quit()

# واجهة المستخدم
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    p_in = col1.text_input("Passport Number", key="s_p")
    n_in = col2.selectbox("Nationality", countries_list, key="s_n")
    d_in = col3.text_input("Date of Birth (DD/MM/YYYY)", key="s_d")

    if st.button("Search Now"):
        if p_in and d_in:
            start_time = time.time()
            progress_bar = st.progress(0)
            status_area = st.empty()
            
            with st.spinner("Searching..."):
                result = extract_data(p_in, n_in, d_in)
                progress_bar.progress(100)
                
                if result:
                    elapsed = round(time.time() - start_time, 2)
                    status_area.success(f"✅ Success: 1 | ⏱️ Live Timer: {elapsed}s")
                    st.dataframe(pd.DataFrame([result]), use_container_width=True)
                else:
                    status_area.error("❌ No results found in MOHRE database for this person.")

with tab2:
    st.subheader("Batch Processing")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if file:
        df_input = pd.read_excel(file)
        st.write("File Preview:")
        st.dataframe(df_input.head(), use_container_width=True)
        
        if st.button("🚀 Start Batch Search"):
            results_list = []
            start_batch = time.time()
            
            progress_bar = st.progress(0)
            stats_area = st.empty()
            table_area = st.empty()
            
            total = len(df_input)
            for i, row in df_input.iterrows():
                # محاكاة استخراج البيانات من الصف
                data = extract_data(str(row[0]), str(row[1]), str(row[2]))
                
                if data:
                    results_list.append(data)
                
                # تحديث العداد والوقت والشريط
                elapsed = round(time.time() - start_batch, 1)
                progress_bar.progress((i + 1) / total)
                stats_area.markdown(f"### ✅ Found: {len(results_list)} / {total} | ⏱️ Timer: {elapsed}s")
                
                if results_list:
                    table_area.dataframe(pd.DataFrame(results_list), use_container_width=True)

            if results_list:
                st.success(f"Batch Completed! {len(results_list)} records extracted.")
                # زر التحميل يظهر هنا بعد الانتهاء
                csv = pd.DataFrame(results_list).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Extracted Data (CSV)",
                    data=csv,
                    file_name=f"MOHRE_Results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("⚠️ Process finished, but no results were found for any record.")
