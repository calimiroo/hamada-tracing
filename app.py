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

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة جلسة العمل ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'show_deep_button' not in st.session_state:
    st.session_state['show_deep_button'] = False
if 'deep_search_in_progress' not in st.session_state:
    st.session_state['deep_search_in_progress'] = False
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None

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

# --- دالة لإنشاء متصفح ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

# --- وظيفة البحث الأساسي ---
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
                return val if val else 'N/A'
            except: return 'N/A'
        
        card_num = get_value("Card Number")
        if card_num == 'N/A': return None
        
        return {
            "Passport Number": passport, 
            "Nationality": nationality, 
            "Date of Birth": dob_str,
            "Job Description": get_value("Job Description"),
            "Card Number": card_num, 
            "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"), 
            "Total Salary": get_value("Total Salary"),
            "Status": "Found",
            "Company Name": "",
            "Company Code": "",
            "Client Name": "",
            "Profession": ""
        }
    except Exception as e:
        st.error(f"Error in search: {str(e)}")
        return None
    finally: 
        driver.quit()

# --- وظيفة البحث العميق ---
def deep_search(card_number):
    """Search for additional information using card number on inquiry.mohre.gov.ae"""
    driver = get_driver()
    try:
        # انتقل إلى الموقع
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)
        
        # انتظر حتى يتم تحميل الصفحة
        wait = WebDriverWait(driver, 10)
        
        # البحث عن القائمة المنسدلة واختيار "Electronic Work Permit Information"
        try:
            select_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
            select = Select(select_element)
            
            # البحث عن الخيار المطلوب
            options = select.options
            option_found = False
            for option in options:
                if "Electronic Work Permit Information" in option.text or "معلومات تصريح العمل الإلكتروني" in option.text:
                    select.select_by_visible_text(option.text)
                    option_found = True
                    time.sleep(2)
                    break
            
            if not option_found:
                st.warning("Could not find 'Electronic Work Permit Information' option")
        except Exception as e:
            st.warning(f"Could not select option: {str(e)}")
        
        # البحث عن حقل إدخال رقم البطاقة
        card_input = None
        
        # محاولة العثور على الحقل بطرق مختلفة
        try:
            card_input = driver.find_element(By.ID, "CardNo")
        except:
            try:
                card_input = driver.find_element(By.NAME, "CardNo")
            except:
                try:
                    card_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'رقم البطاقة')]")
                except:
                    try:
                        card_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Card')]")
                    except:
                        try:
                            # البحث عن أي حقل إدخال
                            inputs = driver.find_elements(By.TAG_NAME, "input")
                            for inp in inputs:
                                if inp.get_attribute("type") == "text":
                                    card_input = inp
                                    break
                        except:
                            pass
        
        if card_input:
            card_input.clear()
            card_input.send_keys(card_number)
            time.sleep(2)
        else:
            st.error("Could not find card number input field")
            return {"Company Name": "Error", "Company Code": "Error", "Client Name": "Error", "Profession": "Error"}
        
        # فك الكابتشا
        captcha_script = """
        javascript:(function(){
            try {
                const tryFill = () => {
                    const code = Array.from(document.querySelectorAll('div,span,b,strong')).map(el => el.innerText.trim()).find(txt => /^\\d{4}$/.test(txt));
                    const input = Array.from(document.querySelectorAll('input')).find(i => i.placeholder.includes("التحقق") || i.placeholder.toLowerCase().includes("captcha"));
                    if(code && input) {
                        input.value = code;
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        return true;
                    }
                    return false;
                };
                
                // حاول 5 مرات
                for(let i = 0; i < 5; i++) {
                    if(tryFill()) break;
                }
            } catch(e) {
                console.error('Error:', e);
            }
        })();
        """
        
        driver.execute_script(captcha_script)
        time.sleep(3)
        
        # البحث عن زر الإرسال
        submit_button = None
        try:
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'بحث') or contains(text(), 'Search')]")
        except:
            try:
                submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
            except:
                pass
        
        if submit_button:
            submit_button.click()
            time.sleep(5)
        
        # استخراج البيانات
        result_data = {
            "Company Name": "Not Found",
            "Company Code": "Not Found", 
            "Client Name": "Not Found",
            "Profession": "Not Found"
        }
        
        # حاول استخراج البيانات من الصفحة
        page_text = driver.page_source
        
        # البحث عن البيانات باستخدام أنماط بسيطة
        import re
        
        # أنماط البحث
        patterns = [
            ("Company Name", ["Company Name", "اسم الشركة", "اسم المنشأة"]),
            ("Company Code", ["Company Code", "كود الشركة", "رقم المنشأة"]),
            ("Client Name", ["Client Name", "اسم العميل", "الاسم"]),
            ("Profession", ["Profession", "المهنة", "الوظيفة"])
        ]
        
        for field_name, search_terms in patterns:
            for term in search_terms:
                pattern = f"{term}[\\s:]*([^<>\n]+)"
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if value:
                        result_data[field_name] = value
                        break
        
        return result_data
        
    except Exception as e:
        st.error(f"Error in deep search: {str(e)}")
        return {
            "Company Name": "Error",
            "Company Code": "Error",
            "Client Name": "Error", 
            "Profession": "Error"
        }
    finally:
        try:
            driver.quit()
        except:
            pass

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    
    # إدخال البيانات
    col1, col2, col3 = st.columns(3)
    passport = col1.text_input("Passport Number", key="single_passport")
    nationality = col2.selectbox("Nationality", ["Select", "Egypt", "India", "Philippines", "Pakistan"], key="single_nationality")
    dob = col3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="single_dob")
    
    # زر البحث الأساسي
    if st.button("Search Now", key="single_search"):
        if passport and nationality != "Select" and dob:
            with st.spinner("Searching..."):
                result = extract_data(passport, nationality, dob.strftime("%d/%m/%Y"))
                if result:
                    st.session_state.single_result = result
                    st.session_state.show_deep_button = True
                else:
                    st.error("No data found")
        else:
            st.error("Please fill all fields")
    
    # عرض نتيجة البحث الأساسي
    if st.session_state.single_result:
        st.success("Search completed!")
        df_result = pd.DataFrame([st.session_state.single_result])
        st.dataframe(df_result)
        
        # زر البحث العميق
        if st.session_state.show_deep_button and st.session_state.single_result.get("Status") == "Found":
            if st.button("🔍 Deep Search", key="single_deep_button"):
                st.session_state.deep_search_in_progress = True
                
                with st.spinner("Performing deep search..."):
                    card_number = st.session_state.single_result.get("Card Number")
                    if card_number and card_number != "N/A":
                        deep_data = deep_search(card_number)
                        
                        # تحديث البيانات
                        st.session_state.single_result.update(deep_data)
                        
                        st.success("Deep search completed!")
                        st.session_state.show_deep_button = False
                        
                        # عرض النتيجة المحدثة
                        updated_df = pd.DataFrame([st.session_state.single_result])
                        st.dataframe(updated_df)
                        
                        # زر التحميل
                        csv = updated_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Result",
                            data=csv,
                            file_name=f"result_{passport}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error("No card number found for deep search")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df.head())
        
        # التحكم في العملية
        col1, col2, col3 = st.columns(3)
        
        if col1.button("▶️ Start Processing", key="batch_start"):
            st.session_state.run_state = 'running'
            st.session_state.start_time_ref = time.time()
            st.session_state.batch_results = []
            st.rerun()
        
        if col2.button("⏹️ Stop", key="batch_stop"):
            st.session_state.run_state = 'stopped'
            st.rerun()
        
        if col3.button("🔄 Reset", key="batch_reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.session_state.show_deep_button = False
            st.rerun()
        
        # معالجة المجموعة
        if st.session_state.run_state == 'running':
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_area = st.empty()
            
            for i, row in df.iterrows():
                if i < len(st.session_state.batch_results):
                    continue
                    
                if st.session_state.run_state == 'stopped':
                    break
                
                passport = str(row.get('Passport Number', '')).strip()
                nationality = str(row.get('Nationality', 'Egypt')).strip()
                dob = str(row.get('Date of Birth', ''))
                
                status_text.info(f"Processing {i+1}/{len(df)}: {passport}")
                
                # تحويل تاريخ الميلاد
                try:
                    dob_date = pd.to_datetime(dob).strftime('%d/%m/%Y')
                except:
                    dob_date = dob
                
                result = extract_data(passport, nationality, dob_date)
                
                if result:
                    st.session_state.batch_results.append(result)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": passport,
                        "Nationality": nationality,
                        "Date of Birth": dob_date,
                        "Job Description": "N/A",
                        "Card Number": "N/A",
                        "Card Issue": "N/A",
                        "Card Expiry": "N/A",
                        "Basic Salary": "N/A",
                        "Total Salary": "N/A",
                        "Status": "Not Found",
                        "Company Name": "N/A",
                        "Company Code": "N/A",
                        "Client Name": "N/A",
                        "Profession": "N/A"
                    })
                
                # تحديث التقدم
                progress_bar.progress((i + 1) / len(df))
                
                # عرض النتائج أولاً بأول
                current_df = pd.DataFrame(st.session_state.batch_results)
                results_area.dataframe(current_df, height=300)
                
                time.sleep(1)
            
            # بعد اكتمال المعالجة
            if len(st.session_state.batch_results) == len(df):
                st.session_state.run_state = 'stopped'
                st.success(f"Batch processing completed! Processed {len(df)} records")
                
                # عرض زر البحث العميق
                found_count = sum(1 for r in st.session_state.batch_results if r.get("Status") == "Found")
                if found_count > 0:
                    st.session_state.show_deep_button = True
        
        # عرض زر البحث العميق للمجموعة
        if st.session_state.show_deep_button and len(st.session_state.batch_results) > 0:
            found_records = [r for r in st.session_state.batch_results if r.get("Status") == "Found"]
            if found_records:
                st.markdown("---")
                st.subheader("Deep Search Options")
                st.write(f"Found {len(found_records)} records with status 'Found'")
                
                if st.button("🔍 Start Deep Search (For Found Records)", key="batch_deep"):
                    st.session_state.deep_search_in_progress = True
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_area = st.empty()
                    
                    # نسخة من النتائج للتحديث
                    updated_results = st.session_state.batch_results.copy()
                    
                    for idx, record in enumerate(found_records):
                        card_number = record.get("Card Number")
                        if card_number and card_number != "N/A":
                            status_text.info(f"Deep searching {idx+1}/{len(found_records)}: Card {card_number}")
                            
                            deep_data = deep_search(card_number)
                            
                            # تحديث السجل
                            for i, original_record in enumerate(updated_results):
                                if original_record.get("Passport Number") == record.get("Passport Number"):
                                    updated_results[i].update(deep_data)
                                    break
                            
                            # تحديث التقدم
                            progress_bar.progress((idx + 1) / len(found_records))
                            
                            # عرض النتائج أولاً بأول
                            current_df = pd.DataFrame(updated_results)
                            results_area.dataframe(current_df, height=400)
                    
                    # حفظ النتائج المحدثة
                    st.session_state.batch_results = updated_results
                    st.session_state.show_deep_button = False
                    
                    st.success(f"Deep search completed for {len(found_records)} records!")
                    
                    # زر تحميل النتائج النهائية
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    csv = final_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download Full Results with Deep Search",
                        data=csv,
                        file_name="full_results_with_deep_search.csv",
                        mime="text/csv",
                        key="final_download"
                    )
        
        # عرض النتائج النهائية
        if len(st.session_state.batch_results) > 0:
            st.markdown("---")
            st.subheader("Results")
            final_df = pd.DataFrame(st.session_state.batch_results)
            st.dataframe(final_df, height=400)
