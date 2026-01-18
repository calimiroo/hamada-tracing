import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import re

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة جلسة العمل (Session State) ---
# إعادة تعيين جميع الحالات عند بداية الجلسة
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
if 'show_batch_deep_button' not in st.session_state:
    st.session_state['show_batch_deep_button'] = False
if 'initial_batch_done' not in st.session_state:
    st.session_state['initial_batch_done'] = False
if 'batch_processing_done' not in st.session_state:
    st.session_state['batch_processing_done'] = False

# قائمة الجنسيات
countries_list = ["Select Nationality", "Egypt", "India", "Philippines", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"]

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

# --- وظيفة البحث العميق (Deep Search) - محسنة ---
def deep_search(card_number):
    driver = None
    try:
        driver = get_driver()
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)
        
        # البحث عن القائمة المنسدلة
        select_found = False
        try:
            selects = driver.find_elements(By.TAG_NAME, "select")
            for select in selects:
                try:
                    select_obj = Select(select)
                    options = [option.text for option in select_obj.options]
                    for option_text in options:
                        if "Electronic Work Permit Information" in option_text or "معلومات تصريح العمل الإلكتروني" in option_text:
                            select_obj.select_by_visible_text(option_text)
                            select_found = True
                            time.sleep(2)
                            break
                    if select_found:
                        break
                except:
                    continue
        except:
            pass
        
        if not select_found:
            # محاولة البحث عن عناصر radio أو checkbox
            try:
                elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information') or contains(text(), 'معلومات تصريح العمل الإلكتروني')]")
                for elem in elements:
                    try:
                        elem.click()
                        time.sleep(2)
                        select_found = True
                        break
                    except:
                        continue
            except:
                pass
        
        # البحث عن حقل رقم البطاقة
        card_input = None
        # محاولات مختلفة للعثور على الحقل
        search_selectors = [
            ("id", "CardNo"),
            ("name", "CardNo"),
            ("xpath", "//input[contains(@placeholder, 'رقم البطاقة')]"),
            ("xpath", "//input[contains(@placeholder, 'Card')]"),
            ("xpath", "//input[@type='text']"),
            ("xpath", "//input")
        ]
        
        for selector_type, selector_value in search_selectors:
            try:
                if selector_type == "id":
                    card_input = driver.find_element(By.ID, selector_value)
                elif selector_type == "name":
                    card_input = driver.find_element(By.NAME, selector_value)
                elif selector_type == "xpath":
                    card_input = driver.find_element(By.XPATH, selector_value)
                
                if card_input:
                    card_input.clear()
                    card_input.send_keys(card_number)
                    time.sleep(2)
                    break
            except:
                continue
        
        # فك الكابتشا
        try:
            captcha_js = """
            javascript:(function(){
                try {
                    const tryFill = () => {
                        const code = Array.from(document.querySelectorAll('div, span, b, strong')).map(el => el.innerText.trim()).find(txt => /^\\d{4}$/.test(txt));
                        const input = Array.from(document.querySelectorAll('input')).find(i => 
                            i.placeholder && (i.placeholder.includes("التحقق") || i.placeholder.toLowerCase().includes("captcha")));
                        if(code && input) {
                            input.value = code;
                            input.dispatchEvent(new Event('input', {bubbles: true}));
                            return true;
                        }
                        return false;
                    };
                    // حاول عدة مرات
                    for(let i = 0; i < 5; i++) {
                        if(tryFill()) break;
                        setTimeout(() => {}, 300);
                    }
                } catch(e) {
                    console.error('Error:', e);
                }
            })();
            """
            driver.execute_script(captcha_js)
            time.sleep(2)
        except:
            pass
        
        # البحث عن زر الإرسال
        try:
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'بحث') or contains(text(), 'Search') or contains(text(), 'Submit')]")
            if not submit_buttons:
                submit_buttons = driver.find_elements(By.XPATH, "//input[@type='submit']")
            
            if submit_buttons:
                submit_buttons[0].click()
                time.sleep(5)
        except:
            pass
        
        # استخراج البيانات
        result_data = {
            "Company Name": "Not Found",
            "Company Code": "Not Found", 
            "Client Name": "Not Found",
            "Profession": "Not Found"
        }
        
        # الحصول على نص الصفحة
        page_text = driver.page_source
        
        # أنماط البحث
        patterns = {
            "Company Name": [
                r'Company Name[\s:]*([^<>\n]+)',
                r'اسم الشركة[\s:]*([^<>\n]+)',
                r'اسم المنشأة[\s:]*([^<>\n]+)',
                r'<td[^>]*>\s*Company Name\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>',
                r'<td[^>]*>\s*اسم الشركة\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>'
            ],
            "Company Code": [
                r'Company Code[\s:]*([^<>\n]+)',
                r'كود الشركة[\s:]*([^<>\n]+)',
                r'رقم المنشأة[\s:]*([^<>\n]+)',
                r'<td[^>]*>\s*Company Code\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>'
            ],
            "Client Name": [
                r'Client Name[\s:]*([^<>\n]+)',
                r'اسم العميل[\s:]*([^<>\n]+)',
                r'<td[^>]*>\s*Client Name\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>'
            ],
            "Profession": [
                r'Profession[\s:]*([^<>\n]+)',
                r'المهنة[\s:]*([^<>\n]+)',
                r'<td[^>]*>\s*Profession\s*</td>\s*<td[^>]*>\s*([^<]+)\s*</td>'
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # تنظيف القيمة
                    value = re.sub(r'<[^>]+>', '', value)  # إزالة tags HTML
                    value = re.sub(r'\s+', ' ', value)  # إزالة المسافات الزائدة
                    if value and value not in ["&nbsp;", "nbsp", "N/A", "null"]:
                        result_data[field] = value
                        break
        
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
        if driver:
            try:
                driver.quit()
            except:
                pass

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    
    # حفظ القيم في session state لتجنب إعادة التعيين
    if 's_p_value' not in st.session_state:
        st.session_state.s_p_value = ""
    if 's_n_value' not in st.session_state:
        st.session_state.s_n_value = "Select Nationality"
    if 's_d_value' not in st.session_state:
        st.session_state.s_d_value = None
    
    c1, c2, c3 = st.columns(3)
    
    p_in = c1.text_input("Passport Number", key="s_p", value=st.session_state.s_p_value)
    n_in = c2.selectbox("Nationality", countries_list, key="s_n", index=countries_list.index(st.session_state.s_n_value) if st.session_state.s_n_value in countries_list else 0)
    d_in = c3.date_input("Date of Birth", value=st.session_state.s_d_value, min_value=datetime(1900,1,1), key="s_d")
    
    # تحديث القيم في session state
    st.session_state.s_p_value = p_in
    st.session_state.s_n_value = n_in
    st.session_state.s_d_value = d_in
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_clicked = st.button("Search Now")
    
    # البحث العميق للبحث الفردي
    deep_search_single_clicked = False
    with col2:
        if st.session_state.single_result and st.session_state.single_result.get("Status") == "Found" and not st.session_state.single_deep_done:
            deep_search_single_clicked = st.button("🔍 Deep Search", key="single_deep_search", type="primary")
    
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
        else:
            st.error("Please fill all fields")
    
    if deep_search_single_clicked and st.session_state.single_result:
        with st.spinner("Performing deep search..."):
            deep_data = deep_search(st.session_state.single_result["Card Number"])
            # تحديث البيانات الأصلية
            st.session_state.single_result.update(deep_data)
            st.session_state.single_deep_done = True
            st.rerun()
    
    # عرض النتيجة النهائية
    if st.session_state.single_result:
        st.success("Search completed!")
        result_df = pd.DataFrame([st.session_state.single_result])
        styled_df = result_df.style.map(color_status, subset=['Status'])
        st.table(styled_df)

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df.head(), height=150)
        
        # التحكم في العملية
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        
        if col_ctrl1.button("▶️ Start / Resume", type="primary"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None:
                st.session_state.start_time_ref = time.time()
            st.session_state.batch_processing_done = False
            st.session_state.deep_search_completed = False
            st.session_state.show_batch_deep_button = False
            st.rerun()
       
        if col_ctrl2.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
            st.rerun()
       
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.session_state.deep_search_completed = False
            st.session_state.batch_processing_done = False
            st.session_state.show_batch_deep_button = False
            st.session_state.initial_batch_done = False
            st.rerun()
        
        # زر البحث العميق للدفعة (يظهر بعد اكتمال المعالجة الأولية)
        if len(st.session_state.batch_results) > 0 and len(st.session_state.batch_results) == len(df):
            if not st.session_state.initial_batch_done:
                st.session_state.initial_batch_done = True
                st.session_state.show_batch_deep_button = True
        
        if st.session_state.show_batch_deep_button and not st.session_state.deep_search_completed:
            found_records = [r for r in st.session_state.batch_results if r.get("Status") == "Found"]
            if found_records:
                st.markdown("---")
                st.subheader("Deep Search Options")
                st.write(f"Found {len(found_records)} records with 'Found' status for deep search")
                
                if st.button("🔍 Start Deep Search (For Found Records Only)", type="primary", key="batch_deep_search"):
                    st.session_state.deep_search_completed = True
                    st.session_state.show_batch_deep_button = False
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_area = st.empty()
                    
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
                        
                        # عرض النتائج أولاً بأول
                        current_df = pd.DataFrame(updated_results)
                        styled_df = current_df.style.map(color_status, subset=['Status'])
                        results_area.dataframe(styled_df, use_container_width=True, height=400)
                    
                    # حفظ النتائج المحدثة
                    st.session_state.batch_results = updated_results
                    status_text.success(f"✅ Deep search completed for {len(found_records)} records!")
                    
                    # زر تحميل النتائج النهائية
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    csv = final_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download Full Report with Deep Search (CSV)",
                        data=csv,
                        file_name="full_results_with_deep_search.csv",
                        mime="text/csv",
                        key="download_final"
                    )
        
        # المعالجة الرئيسية
        if st.session_state.run_state in ['running', 'paused']:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            results_area = st.empty()
           
            actual_success = 0
            
            # احسب عدد السجلات التي تمت معالجتها بالفعل
            processed_count = len(st.session_state.batch_results)
           
            for i in range(processed_count, len(df)):
                while st.session_state.run_state == 'paused':
                    status_text.warning("⏸️ Paused... click Resume to continue.")
                    time.sleep(1)
               
                if st.session_state.run_state == 'stopped':
                    break
                    
                row = df.iloc[i]
                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                try: 
                    dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: 
                    dob = str(row.get('Date of Birth', ''))
                    
                status_text.info(f"🔍 Processing {i+1}/{len(df)}: {p_num}")
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
                results_area.dataframe(styled_df, use_container_width=True, height=400)
            
            # عند اكتمال المعالجة
            if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
                st.session_state.run_state = 'stopped'
                st.session_state.batch_processing_done = True
                
                st.success(f"✅ Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
                
                # زر تحميل النتائج الأولية
                if not st.session_state.deep_search_completed:
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    csv = final_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download Initial Report (CSV)",
                        data=csv,
                        file_name="initial_results.csv",
                        mime="text/csv",
                        key="download_initial"
                    )
                
                st.rerun()
        
        # عرض النتائج النهائية إذا كانت موجودة
        if len(st.session_state.batch_results) > 0:
            st.markdown("---")
            st.subheader("Results")
            final_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = final_df.style.map(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True, height=400)
