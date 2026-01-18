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
    st.session_state.authenticated = False
if 'run_state' not in st.session_state:
    st.session_state.run_state = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'single_result' not in st.session_state:
    st.session_state.single_result = None
if 'show_deep_button' not in st.session_state:
    st.session_state.show_deep_button = False
if 'deep_completed' not in st.session_state:
    st.session_state.deep_completed = False

# قائمة الجنسيات الكاملة
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- تسجيل الدخول ---
if not st.session_state.authenticated:
    with st.form("login_form"):
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Bilkish":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password.")
    st.stop()

# --- وظائف المساعدة ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    if val == 'Found':
        return 'background-color: #28a745; color: white'
    else:
        return 'background-color: #dc3545; color: white'

# --- البحث الأساسي ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        
        # إدخال رقم الجواز
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        
        # اختيار الجنسية
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items:
            items[0].click()
        
        # إدخال تاريخ الميلاد
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        
        # النقر على زر البحث
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)
        
        # استخراج البيانات
        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                element = driver.find_element(By.XPATH, xpath)
                return element.text.strip() if element.text.strip() else 'N/A'
            except:
                return 'N/A'
        
        card_num = get_value("Card Number")
        if card_num == 'N/A':
            return None
        
        # ترجمة الوظيفة
        job_desc = get_value("Job Description")
        try:
            if job_desc != 'N/A' and job_desc:
                job_desc = GoogleTranslator(source='auto', target='en').translate(job_desc)
        except:
            pass
        
        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": job_desc,
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

# --- البحث العميق ---
def deep_search(card_number):
    driver = get_driver()
    try:
        # الانتقال إلى موقع الاستعلام
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)
        
        # انتظار تحميل الصفحة
        wait = WebDriverWait(driver, 10)
        
        # محاولة اختيار "Electronic Work Permit Information" من القائمة المنسدلة
        try:
            # البحث عن جميع عناصر select
            select_elements = driver.find_elements(By.TAG_NAME, "select")
            for select_element in select_elements:
                try:
                    select = Select(select_element)
                    # البحث عن الخيار المطلوب
                    for option in select.options:
                        if "Electronic Work Permit Information" in option.text:
                            select.select_by_visible_text(option.text)
                            time.sleep(2)
                            break
                except:
                    continue
        except:
            pass
        
        # البحث عن حقل إدخال رقم البطاقة
        card_input = None
        
        # محاولات مختلفة للعثور على الحقل
        try:
            card_input = wait.until(EC.presence_of_element_located((By.ID, "CardNo")))
        except:
            try:
                card_input = driver.find_element(By.NAME, "CardNo")
            except:
                try:
                    card_input = driver.find_element(By.XPATH, "//input[@placeholder='رقم البطاقة' or @placeholder='Card Number']")
                except:
                    try:
                        # البحث عن أي حقل إدخال نصي
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        for inp in inputs:
                            if inp.get_attribute("type") == "text":
                                card_input = inp
                                break
                    except:
                        pass
        
        if card_input:
            try:
                card_input.clear()
                card_input.send_keys(card_number)
                time.sleep(2)
            except:
                # محاولة باستخدام JavaScript
                driver.execute_script(f"arguments[0].value = '{card_number}';", card_input)
                time.sleep(2)
        
        # فك الكابتشا باستخدام JavaScript
        captcha_script = """
        javascript:(function(){
            try {
                const tryFill = () => {
                    const code = Array.from(document.querySelectorAll('div,span,b,strong')).map(el => el.innerText.trim()).find(txt => /^\\d{4}$/.test(txt));
                    const input = Array.from(document.querySelectorAll('input')).find(i => i.placeholder && (i.placeholder.includes("التحقق") || i.placeholder.toLowerCase().includes("captcha")));
                    if(code && input) {
                        input.value = code;
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        return true;
                    }
                    return false;
                };
                
                // حاول 3 مرات
                for(let i = 0; i < 3; i++) {
                    if(tryFill()) break;
                }
            } catch(e) {
                console.error('Error in captcha:', e);
            }
        })();
        """
        
        driver.execute_script(captcha_script)
        time.sleep(3)
        
        # البحث عن زر الإرسال
        try:
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'بحث') or contains(text(), 'Search') or @type='submit']")
            submit_button.click()
        except:
            try:
                submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                submit_button.click()
            except:
                # إذا لم يتم العثور على زر، حاول باستخدام JavaScript
                driver.execute_script("document.querySelector('form').submit();")
        
        time.sleep(5)
        
        # استخراج البيانات من النتيجة
        result = {
            "Company Name": "Not Found",
            "Company Code": "Not Found", 
            "Client Name": "Not Found",
            "Profession": "Not Found"
        }
        
        # الحصول على محتوى الصفحة
        page_source = driver.page_source
        
        # البحث عن البيانات باستخدام regex
        import re
        
        # أنماط البحث المختلفة
        patterns = {
            "Company Name": [
                r'Company Name[\s:]*([^<\n]+)',
                r'اسم الشركة[\s:]*([^<\n]+)',
                r'اسم المنشأة[\s:]*([^<\n]+)',
                r'<td[^>]*>.*Company Name.*</td>\s*<td[^>]*>(.*?)</td>',
                r'<td[^>]*>.*اسم الشركة.*</td>\s*<td[^>]*>(.*?)</td>'
            ],
            "Company Code": [
                r'Company Code[\s:]*([^<\n]+)',
                r'كود الشركة[\s:]*([^<\n]+)',
                r'رقم المنشأة[\s:]*([^<\n]+)'
            ],
            "Client Name": [
                r'Client Name[\s:]*([^<\n]+)',
                r'اسم العميل[\s:]*([^<\n]+)',
                r'الاسم[\s:]*([^<\n]+)'
            ],
            "Profession": [
                r'Profession[\s:]*([^<\n]+)',
                r'المهنة[\s:]*([^<\n]+)',
                r'الوظيفة[\s:]*([^<\n]+)'
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if matches:
                    value = matches[0].strip()
                    # تنظيف القيمة
                    value = re.sub(r'<[^>]+>', '', value)
                    value = re.sub(r'\s+', ' ', value)
                    if value and len(value) > 1:
                        result[field] = value
                        break
        
        return result
        
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

# --- الواجهة الرئيسية ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    
    col1, col2, col3 = st.columns(3)
    passport = col1.text_input("Passport Number", key="single_passport")
    nationality = col2.selectbox("Nationality", countries_list, key="single_nationality")
    dob = col3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="single_dob")
    
    search_col, deep_col = st.columns(2)
    
    with search_col:
        if st.button("Search Now", type="primary", key="single_search"):
            if passport and nationality != "Select Nationality" and dob:
                with st.spinner("Searching..."):
                    result = extract_data(passport, nationality, dob.strftime("%d/%m/%Y"))
                    if result:
                        st.session_state.single_result = result
                        st.session_state.show_deep_button = True
                        st.success("Search completed!")
                    else:
                        st.error("No data found")
                        st.session_state.single_result = None
                        st.session_state.show_deep_button = False
            else:
                st.error("Please fill all fields")
    
    # عرض نتيجة البحث الأساسي
    if st.session_state.single_result:
        df_result = pd.DataFrame([st.session_state.single_result])
        styled_df = df_result.style.map(color_status, subset=['Status'])
        st.table(styled_df)
        
        # زر البحث العميق
        if st.session_state.show_deep_button and st.session_state.single_result.get("Status") == "Found":
            with deep_col:
                if st.button("🔍 Deep Search", type="secondary", key="single_deep"):
                    with st.spinner("Performing deep search..."):
                        card_number = st.session_state.single_result.get("Card Number")
                        if card_number and card_number != "N/A":
                            deep_data = deep_search(card_number)
                            
                            # تحديث البيانات
                            st.session_state.single_result.update(deep_data)
                            st.session_state.show_deep_button = False
                            
                            # عرض النتيجة المحدثة
                            updated_df = pd.DataFrame([st.session_state.single_result])
                            styled_updated = updated_df.style.map(color_status, subset=['Status'])
                            st.table(styled_updated)
                            
                            # زر التحميل
                            csv = updated_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Result",
                                data=csv,
                                file_name=f"result_{passport}.csv",
                                mime="text/csv",
                                key="download_single"
                            )
                        else:
                            st.error("No valid card number found")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df.head(), height=200)
        
        # التحكم في العملية
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Start Processing", type="primary", key="batch_start"):
                st.session_state.run_state = 'running'
                st.session_state.batch_results = []
                st.rerun()
        
        with col2:
            if st.button("⏸️ Pause", key="batch_pause"):
                st.session_state.run_state = 'paused'
                st.rerun()
        
        with col3:
            if st.button("⏹️ Stop & Reset", key="batch_reset"):
                st.session_state.run_state = 'stopped'
                st.session_state.batch_results = []
                st.session_state.deep_completed = False
                st.session_state.show_deep_button = False
                st.rerun()
        
        # معالجة الدفعة
        if st.session_state.run_state == 'running':
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_area = st.empty()
            
            for i, row in df.iterrows():
                if st.session_state.run_state == 'paused':
                    status_text.warning("Processing paused")
                    time.sleep(1)
                    continue
                
                if st.session_state.run_state == 'stopped':
                    break
                
                # تخطي السجلات المعالجة مسبقاً
                if i < len(st.session_state.batch_results):
                    continue
                
                passport = str(row.get('Passport Number', '')).strip()
                nationality = str(row.get('Nationality', '')).strip()
                dob = row.get('Date of Birth')
                
                # تحويل تاريخ الميلاد
                try:
                    if isinstance(dob, str):
                        dob_formatted = dob
                    else:
                        dob_formatted = pd.to_datetime(dob).strftime('%d/%m/%Y')
                except:
                    dob_formatted = str(dob)
                
                status_text.info(f"Processing {i+1}/{len(df)}: {passport}")
                
                result = extract_data(passport, nationality, dob_formatted)
                
                if result:
                    st.session_state.batch_results.append(result)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": passport,
                        "Nationality": nationality,
                        "Date of Birth": dob_formatted,
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
                styled_current = current_df.style.map(color_status, subset=['Status'])
                results_area.dataframe(styled_current, height=400)
                
                time.sleep(1)
            
            # بعد اكتمال المعالجة
            if len(st.session_state.batch_results) == len(df):
                st.session_state.run_state = 'stopped'
                st.success(f"✅ Batch processing completed! Processed {len(df)} records")
                st.session_state.show_deep_button = True
        
        # زر البحث العميق للدفعة
        if st.session_state.show_deep_button and len(st.session_state.batch_results) > 0:
            st.markdown("---")
            st.subheader("Deep Search Options")
            
            found_records = [r for r in st.session_state.batch_results if r.get("Status") == "Found"]
            if found_records:
                st.write(f"Found **{len(found_records)}** records with status 'Found'")
                
                if st.button("🔍 Start Deep Search (For Found Records Only)", type="primary", key="batch_deep"):
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
                            styled_current = current_df.style.map(color_status, subset=['Status'])
                            results_area.dataframe(styled_current, height=400)
                    
                    # حفظ النتائج المحدثة
                    st.session_state.batch_results = updated_results
                    st.session_state.deep_completed = True
                    st.session_state.show_deep_button = False
                    
                    st.success(f"✅ Deep search completed for {len(found_records)} records!")
                    
                    # زر تحميل النتائج النهائية
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    csv = final_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download Full Results with Deep Search",
                        data=csv,
                        file_name="full_results_with_deep_search.csv",
                        mime="text/csv",
                        key="download_final"
                    )
        
        # عرض النتائج النهائية
        if len(st.session_state.batch_results) > 0:
            st.markdown("---")
            st.subheader("Results")
            final_df = pd.DataFrame(st.session_state.batch_results)
            styled_final = final_df.style.map(color_status, subset=['Status'])
            st.dataframe(styled_final, height=400)
            
            # زر تحميل النتائج الأولية
            if not st.session_state.deep_completed:
                csv = final_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Initial Results",
                    data=csv,
                    file_name="initial_results.csv",
                    mime="text/csv",
                    key="download_initial"
                )
