import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from deep_translator import GoogleTranslator
import re

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Debugger", layout="wide")
st.title("HAMADA TRACING - VISUAL DEBUG MODE")

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

# قائمة الجنسيات
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

# --- وظيفة إعداد المتصفح (تعديل لتشغيل الواجهة الرسومية) ---
def get_driver():
    options = uc.ChromeOptions()
    # تم إزالة headless لكي ترى المتصفح
    options.add_argument("--start-maximized") # تكبير النافذة لرؤية العناصر بوضوح
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # headless=False هو المفتاح هنا
    driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
    return driver

def color_status(val):
    if val == 'Found':
        return 'background-color: #28a745; color: white'
    else:
        return 'background-color: #dc3545; color: white'

# --- البحث الأساسي ---
def extract_data(passport, nationality, dob_str):
    driver = None
    try:
        driver = get_driver()
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3) # وقت لكي ترى الصفحة تحمل
        
        # إدخال رقم الجواز
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        
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
        
        # زيادة وقت الانتظار لكي ترى النتائج بنفسك
        time.sleep(6)
        
        # استخراج البيانات
        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                element = driver.find_element(By.XPATH, xpath)
                return element.text.strip() if element.text.strip() else 'N/A'
            except:
                return 'N/A'
        
        card_num = get_value("Card Number")
        if card_num == 'N/A' or not card_num:
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
        st.error(f"Basic Search Error: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# --- البحث العميق (Deep Search) - هنا سترى المشكلة بوضوح ---
def deep_search(card_number):
    driver = None
    result_data = {
        "Company Name": "Not Found",
        "Company Code": "Not Found", 
        "Client Name": "Not Found",
        "Profession": "Not Found"
    }
    
    try:
        driver = get_driver()
        driver.get("https://inquiry.mohre.gov.ae/")
        
        wait = WebDriverWait(driver, 20) # زيادة وقت الانتظار
        
        # 1. اختيار Electronic Work Permit Information
        time.sleep(2) # راقب هنا هل سيختار القائمة؟
        try:
            select_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
            select = Select(select_element)
            select.select_by_visible_text("Electronic Work Permit Information")
            time.sleep(1)
        except Exception as e:
            # محاولة جافا سكريبت إذا فشل الاختيار العادي
            driver.execute_script("""
                var options = document.querySelectorAll('option');
                for(var i=0; i<options.length; i++) {
                    if(options[i].text.includes('Electronic Work Permit') || options[i].text.includes('تصريح العمل الإلكتروني')) {
                        options[i].parentElement.value = options[i].value;
                        options[i].parentElement.dispatchEvent(new Event('change'));
                        break;
                    }
                }
            """)
        
        time.sleep(3) # راقب ظهور حقل رقم البطاقة

        # 2. إدخال رقم البطاقة
        card_input = None
        try:
            # محاولة العثور على حقل الإدخال بعدة طرق
            card_input = driver.find_element(By.XPATH, "//input[@id='CardNo' or contains(@placeholder, 'Card') or contains(@placeholder, 'بطاقة')]")
        except:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.is_displayed() and inp.get_attribute("type") == "text" and "captcha" not in str(inp.get_attribute("id")).lower():
                    card_input = inp
                    break
        
        if card_input:
            card_input.clear()
            card_input.send_keys(card_number)
            time.sleep(1) # تأكد من كتابة الرقم
        else:
            st.error("لم يتم العثور على حقل رقم البطاقة")
            return result_data

        # 3. فك الكابتشا
        # الشفرة الخاصة بك
        captcha_script = """
        (function(){
            try{
                const tryFill=()=>{
                    const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\\d{4}$/.test(txt));
                    const input=Array.from(document.querySelectorAll('input')).find(i=>(i.placeholder && (i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"))) || (i.id && i.id.toLowerCase().includes("captcha")));
                    if(code&&input){
                        input.value=code;
                        input.dispatchEvent(new Event('input',{bubbles:true}));
                        return true;
                    }
                    return false;
                };
                tryFill();
            }catch(e){console.error('Error:',e);}
        })();
        """
        driver.execute_script(captcha_script)
        time.sleep(4) # وقت كافي لتتأكد من أن الكابتشا كتبت

        # 4. الضغط على زر البحث
        try:
            search_btn = driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Search') or contains(text(), 'بحث')] | //input[@type='submit']")
            search_btn.click()
        except:
            driver.execute_script("document.forms[0].submit()")
            
        time.sleep(6) # وقت كافي لرؤية النتائج

        # 5. استخراج البيانات
        page_source = driver.page_source
        
        def extract_by_pattern(patterns, source):
            for pattern in patterns:
                match = re.search(pattern, source, re.IGNORECASE | re.DOTALL)
                if match:
                    clean_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                    return clean_text
            return "Not Found"

        company_patterns = [r"Company Name.*?<td[^>]*>(.*?)</td>", r"اسم المنشأة.*?<td[^>]*>(.*?)</td>", r"Company Name\s*:\s*([^<\n]+)"]
        code_patterns = [r"Company Code.*?<td[^>]*>(.*?)</td>", r"رقم المنشأة.*?<td[^>]*>(.*?)</td>", r"Company Code\s*:\s*(\d+)"]
        client_patterns = [r"Person Name.*?<td[^>]*>(.*?)</td>", r"الاسم.*?<td[^>]*>(.*?)</td>", r"Name\s*:\s*([^<\n]+)"]
        profession_patterns = [r"Profession.*?<td[^>]*>(.*?)</td>", r"المهنة.*?<td[^>]*>(.*?)</td>", r"Job\s*:\s*([^<\n]+)"]

        try:
            tds = driver.find_elements(By.TAG_NAME, "td")
            for i, td in enumerate(tds):
                txt = td.text.strip()
                if "Company Name" in txt or "اسم المنشأة" in txt:
                    if i+1 < len(tds): result_data["Company Name"] = tds[i+1].text.strip()
                if "Company Code" in txt or "رقم المنشأة" in txt:
                    if i+1 < len(tds): result_data["Company Code"] = tds[i+1].text.strip()
                if "Person Name" in txt or "الاسم" in txt:
                    if i+1 < len(tds): result_data["Client Name"] = tds[i+1].text.strip()
                if "Profession" in txt or "المهنة" in txt:
                    if i+1 < len(tds): result_data["Profession"] = tds[i+1].text.strip()
        except:
            pass

        if result_data["Company Name"] == "Not Found": result_data["Company Name"] = extract_by_pattern(company_patterns, page_source)
        if result_data["Company Code"] == "Not Found": result_data["Company Code"] = extract_by_pattern(code_patterns, page_source)
        if result_data["Client Name"] == "Not Found": result_data["Client Name"] = extract_by_pattern(client_patterns, page_source)
        if result_data["Profession"] == "Not Found": result_data["Profession"] = extract_by_pattern(profession_patterns, page_source)
            
    except Exception as e:
        st.error(f"Deep Search Error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return result_data

# --- الواجهة الرئيسية ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

# === Tab 1: Single Search ===
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
                with st.spinner("Searching... Check popup window"):
                    result = extract_data(passport, nationality, dob.strftime("%d/%m/%Y"))
                    if result:
                        st.session_state.single_result = result
                        st.session_state.show_deep_button = True
                        st.success("Search completed!")
                    else:
                        st.error("No data found")
                        st.session_state.single_result = None
            else:
                st.error("Please fill all fields")
    
    if st.session_state.single_result:
        df_result = pd.DataFrame([st.session_state.single_result])
        styled_df = df_result.style.map(color_status, subset=['Status'])
        st.table(styled_df)
        
        if st.session_state.show_deep_button and st.session_state.single_result.get("Status") == "Found":
            with deep_col:
                if st.button("🔍 Deep Search", type="secondary", key="single_deep"):
                    card_number = st.session_state.single_result.get("Card Number")
                    if card_number and card_number != "N/A":
                        with st.spinner(f"Opening browser for Card: {card_number}..."):
                            deep_data = deep_search(card_number)
                            st.session_state.single_result.update(deep_data)
                            st.session_state.show_deep_button = False
                            st.rerun()
                    else:
                        st.error("No Card Number found.")

# === Tab 2: Batch Processing ===
with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records: {len(df)}")
        st.dataframe(df.head(), height=150)
        
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
                st.rerun()
        
        results_area = st.empty()
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        if st.session_state.run_state == 'running':
            if st.session_state.batch_results:
                current_df = pd.DataFrame(st.session_state.batch_results)
                results_area.dataframe(current_df.style.map(color_status, subset=['Status']), height=400)

            for i, row in df.iterrows():
                if st.session_state.run_state != 'running': break
                if i < len(st.session_state.batch_results): continue
                
                passport = str(row.get('Passport Number', '')).strip()
                nationality = str(row.get('Nationality', '')).strip()
                dob_raw = row.get('Date of Birth')
                
                try:
                    if isinstance(dob_raw, str): dob_formatted = dob_raw
                    else: dob_formatted = pd.to_datetime(dob_raw).strftime('%d/%m/%Y')
                except: dob_formatted = str(dob_raw)
                
                status_text.info(f"Processing {i+1}/{len(df)}: {passport} - Watch Browser Window")
                
                res = extract_data(passport, nationality, dob_formatted)
                
                if not res:
                    res = {
                        "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_formatted,
                        "Status": "Not Found", "Card Number": "N/A", "Job Description": "N/A",
                        "Card Issue": "N/A", "Card Expiry": "N/A", "Basic Salary": "N/A", "Total Salary": "N/A",
                        "Company Name": "", "Company Code": "", "Client Name": "", "Profession": ""
                    }
                
                st.session_state.batch_results.append(res)
                current_df = pd.DataFrame(st.session_state.batch_results)
                results_area.dataframe(current_df.style.map(color_status, subset=['Status']), height=400)
                progress_bar.progress((i + 1) / len(df))
                
            if len(st.session_state.batch_results) == len(df):
                st.session_state.run_state = 'stopped'
                st.success("Initial Search Completed!")
                st.session_state.show_deep_button = True
                st.rerun()

        if len(st.session_state.batch_results) > 0:
            final_df = pd.DataFrame(st.session_state.batch_results)
            results_area.dataframe(final_df.style.map(color_status, subset=['Status']), height=400)
            
            found_count = len(final_df[final_df['Status'] == 'Found'])
            
            if st.session_state.show_deep_button and found_count > 0:
                st.markdown("---")
                if st.button(f"🔍 Deep Search for {found_count} Found Records", type="primary", key="batch_deep_btn"):
                    st.session_state.run_state = 'deep_searching'
                    st.rerun()
            
            if st.session_state.run_state == 'deep_searching':
                progress_bar.progress(0)
                results_list = st.session_state.batch_results
                total_found = len([x for x in results_list if x['Status'] == 'Found'])
                processed_count = 0
                
                for idx, record in enumerate(results_list):
                    if record['Status'] == 'Found' and record.get('Company Name') == "":
                        card = record.get('Card Number')
                        if card and card != "N/A":
                            status_text.info(f"Deep Searching Card: {card}... Check Browser")
                            deep_data = deep_search(card)
                            results_list[idx].update(deep_data)
                            st.session_state.batch_results = results_list
                            results_area.dataframe(pd.DataFrame(results_list).style.map(color_status, subset=['Status']), height=400)
                            processed_count += 1
                            progress_bar.progress(processed_count / total_found)
                
                st.session_state.run_state = 'stopped'
                st.session_state.deep_completed = True
                st.session_state.show_deep_button = False
                st.success("Deep Search Completed!")
                st.rerun()

            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Final Results",
                data=csv,
                file_name="final_results_visual.csv",
                mime="text/csv",
                key="final_download"
            )
