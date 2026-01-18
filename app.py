import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'deep_search_completed' not in st.session_state:
    st.session_state['deep_search_completed'] = False
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'single_deep_done' not in st.session_state:
    st.session_state['single_deep_done'] = False
if 'batch_processing_done' not in st.session_state:
    st.session_state['batch_processing_done'] = False

# قائمة الجنسيات (مختصرة للاختصار)
countries_list = ["Select Nationality", "Egypt", "India", "Philippines", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal", "Afghanistan", "Algeria", "Morocco", "Tunisia", "Sudan", "Syria", "Jordan", "Lebanon", "Palestine State", "Yemen", "Oman", "Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Bahrain"]

# --- تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Incorrect Password.")
    st.stop()

# --- دالة تحويل الوقت ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

# --- وظائف الاستخراج والترجمة ---
def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
       
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)
        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'
        card_num = get_value("Card Number")
        if card_num == 'Not Found': return None
        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num, "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"),
            "Status": "Found",
            "Company Name": "",
            "Company Code": "",
            "Client Name": "",
            "Profession": ""
        }
    except Exception as e:
        print(f"Error in extract_data: {e}")
        return None
    finally: driver.quit()

# --- وظيفة البحث العميق (Deep Search) ---
def deep_search(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(3)
        
        # اختيار "Electronic Work Permit Information"
        try:
            select_element = driver.find_element(By.ID, "ddlServices")
            select = Select(select_element)
            select.select_by_visible_text("Electronic Work Permit Information")
            time.sleep(2)
        except:
            pass
        
        # البحث عن حقل إدخال رقم البطاقة
        card_input = None
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            id_attr = inp.get_attribute("id") or ""
            name_attr = inp.get_attribute("name") or ""
            
            if "card" in placeholder.lower() or "card" in id_attr.lower() or "card" in name_attr.lower():
                card_input = inp
                break
        
        if not card_input:
            try:
                card_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'رقم البطاقة') or contains(@placeholder, 'Card')]")
            except:
                text_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
                if text_inputs:
                    card_input = text_inputs[0]
        
        if card_input:
            card_input.clear()
            card_input.send_keys(card_number)
            time.sleep(2)
        
        # فك الكابتشا باستخدام الكود المقدم
        captcha_js = """
        javascript:(function(){try{const tryFill=()=>{const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\\d{4}$/.test(txt));const input=Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"));if(code&&input){input.value=code;input.dispatchEvent(new Event('input',{bubbles:true}));}else{setTimeout(tryFill,500);}};tryFill();}catch(e){console.error('Error:',e);}})();
        """
        
        driver.execute_script(captcha_js)
        time.sleep(3)
        
        # البحث عن زر الإرسال والضغط عليه
        submit_button = None
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            text = btn.text.lower()
            if "submit" in text or "بحث" in text or "send" in text:
                submit_button = btn
                break
        
        if not submit_button:
            try:
                submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            except:
                try:
                    submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                except:
                    pass
        
        if submit_button:
            submit_button.click()
            time.sleep(5)
        
        # استخراج البيانات من النتيجة
        result_data = {
            "Company Name": "Not Found",
            "Company Code": "Not Found", 
            "Client Name": "Not Found",
            "Profession": "Not Found"
        }
        
        # محاولة استخراج البيانات من الجدول
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if "company" in label or "شركة" in label:
                            result_data["Company Name"] = value
                        elif "code" in label or "رمز" in label:
                            result_data["Company Code"] = value
                        elif "client" in label or "عميل" in label or "name" in label:
                            result_data["Client Name"] = value
                        elif "profession" in label or "مهنة" in label:
                            result_data["Profession"] = value
        except:
            pass
        
        # محاولة أخرى للبحث باستخدام العناصر div
        try:
            page_text = driver.page_source.lower()
            if "company name" in page_text or "اسم الشركة" in page_text:
                result_data["Company Name"] = "Extracted"
            if "company code" in page_text or "كود الشركة" in page_text:
                result_data["Company Code"] = "Extracted"
            if "client name" in page_text or "اسم العميل" in page_text:
                result_data["Client Name"] = "Extracted"
            if "profession" in page_text or "المهنة" in page_text:
                result_data["Profession"] = "Extracted"
        except:
            pass
        
        return result_data
        
    except Exception as e:
        print(f"Error in deep_search: {e}")
        return {
            "Company Name": "Error",
            "Company Code": "Error",
            "Client Name": "Error", 
            "Profession": "Error"
        }
    finally:
        driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    search_clicked = st.button("Search Now")
    
    # زر البحث العميق للبحث الفردي
    deep_search_clicked = False
    if st.session_state.single_result and st.session_state.single_result.get("Status") == "Found" and not st.session_state.single_deep_done:
        deep_search_clicked = st.button("🔍 Deep Search", key="single_deep_search")
    
    if search_clicked:
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res: 
                    st.session_state.single_result = res
                    st.session_state.single_deep_done = False
                    st.rerun()
                else: 
                    st.error("No data found.")
                    st.session_state.single_result = None
                    st.session_state.single_deep_done = False
    
    if deep_search_clicked and st.session_state.single_result:
        with st.spinner("Performing deep search..."):
            deep_data = deep_search(st.session_state.single_result["Card Number"])
            # تحديث البيانات الأصلية
            st.session_state.single_result.update(deep_data)
            st.session_state.single_deep_done = True
            st.rerun()
    
    # عرض النتيجة النهائية
    if st.session_state.single_result:
        result_df = pd.DataFrame([st.session_state.single_result])
        styled_df = result_df.style.map(color_status, subset=['Status'])
        st.table(styled_df)

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df, height=150)
        
        # التحكم في العملية
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        
        if col_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None:
                st.session_state.start_time_ref = time.time()
            st.session_state.batch_processing_done = False
       
        if col_ctrl2.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
       
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.session_state.deep_search_completed = False
            st.session_state.batch_processing_done = False
            st.rerun()
        
        # البحث العميق للدفعة
        if len(st.session_state.batch_results) > 0 and not st.session_state.deep_search_completed:
            found_records = [r for r in st.session_state.batch_results if r.get("Status") == "Found"]
            if found_records:
                if st.button("🔍 Deep Search (For Found Records Only)", key="batch_deep_search"):
                    st.session_state.deep_search_completed = True
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    live_table_area = st.empty()
                    
                    # تحديث النتائج
                    updated_results = st.session_state.batch_results.copy()
                    
                    for idx, record in enumerate(found_records):
                        status_text.info(f"Deep searching {idx+1}/{len(found_records)}: Card {record.get('Card Number', 'N/A')}")
                        
                        deep_data = deep_search(record.get("Card Number", ""))
                        
                        # تحديث السجل الأصلي
                        for i, original_record in enumerate(updated_results):
                            if original_record.get("Passport Number") == record.get("Passport Number"):
                                updated_results[i].update(deep_data)
                                break
                        
                        progress_bar.progress((idx + 1) / len(found_records))
                        
                        # تحديث الجدول أولاً بأول
                        current_df = pd.DataFrame(updated_results)
                        styled_df = current_df.style.map(color_status, subset=['Status'])
                        live_table_area.dataframe(styled_df, use_container_width=True)
                    
                    # حفظ النتائج المحدثة
                    st.session_state.batch_results = updated_results
                    status_text.success(f"Deep search completed for {len(found_records)} records!")
                    
                    # زر تحميل النتائج
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    st.download_button(
                        "📥 Download Full Report (CSV)", 
                        final_df.to_csv(index=False).encode('utf-8'), 
                        "full_results_with_deep_search.csv",
                        mime="text/csv"
                    )
        
        # المعالجة الرئيسية
        if st.session_state.run_state in ['running', 'paused']:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            live_table_area = st.empty()
           
            actual_success = 0
           
            for i, row in df.iterrows():
                while st.session_state.run_state == 'paused':
                    status_text.warning("Paused... click Resume to continue.")
                    time.sleep(1)
               
                if st.session_state.run_state == 'stopped':
                    break
               
                # تخطي ما تمت معالجته
                if i < len(st.session_state.batch_results):
                    if st.session_state.batch_results[i].get("Status") == "Found":
                        actual_success += 1
                    continue
                    
                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                try: 
                    dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: 
                    dob = str(row.get('Date of Birth', ''))
                    
                status_text.info(f"Processing {i+1}/{len(df)}: {p_num}")
                res = extract_data(p_num, nat, dob)
               
                if res:
                    actual_success += 1
                    st.session_state.batch_results.append(res)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                        "Job Description": "N/A", "Card Number": "N/A", "Card Issue": "N/A",
                        "Card Expiry": "N/A", "Basic Salary": "N/A", "Total Salary": "N/A",
                        "Status": "Not Found",
                        "Company Name": "N/A",
                        "Company Code": "N/A",
                        "Client Name": "N/A",
                        "Profession": "N/A"
                    })
                
                # حساب الوقت الكلي
                if st.session_state.start_time_ref:
                    elapsed_seconds = time.time() - st.session_state.start_time_ref
                    time_str = format_time(elapsed_seconds)
                else:
                    time_str = "0:00:00"
               
                progress_bar.progress((i + 1) / len(df))
                stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** {time_str}")
               
                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                live_table_area.dataframe(styled_df, use_container_width=True)
            
            # عند اكتمال المعالجة
            if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
                st.session_state.batch_processing_done = True
                st.success(f"Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
                final_df = pd.DataFrame(st.session_state.batch_results)
                
                # زر تحميل النتائج النهائية
                st.download_button(
                    "📥 Download Initial Report (CSV)", 
                    final_df.to_csv(index=False).encode('utf-8'), 
                    "initial_results.csv",
                    mime="text/csv"
                )
                
                # إعادة تعيين حالة التشغيل لعرض زر البحث العميق
                st.session_state.run_state = 'stopped'
                st.rerun()
        
        # عرض النتائج النهائية إذا كانت موجودة
        if len(st.session_state.batch_results) > 0:
            final_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = final_df.style.map(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
