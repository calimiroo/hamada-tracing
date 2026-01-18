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
import os

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Tracer", layout="wide")
st.title("HAMADA TRACING - CLOUD MODE")

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

# --- وظيفة المتصفح المصححة للكلاود ---
def get_driver():
    options = uc.ChromeOptions()
    # أهم الإعدادات لتشغيل الكود على السيرفرات
    options.add_argument("--headless=new")  # وضع التخفي الجديد والأكثر ثباتاً
    options.add_argument("--no-sandbox")   # ضروري جداً لبيئة اللينكس
    options.add_argument("--disable-dev-shm-usage") # يمنع استهلاك الذاكرة العشوائية بشكل خاطئ
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # محاولة التشغيل مع معالجة الأخطاء
    try:
        driver = uc.Chrome(options=options, headless=True, use_subprocess=True, version_main=None)
    except Exception as e:
        # محاولة احتياطية في حالة فشل النسخة التلقائية
        st.warning("Retrying driver initialization...")
        driver = uc.Chrome(options=options, headless=True)
        
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
        
        # إدخال رقم الجواز
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        
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
        
        # انتظار النتائج
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Card Number')]"))
            )
        except:
            return None # لم يتم العثور على نتائج
        
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
        # تسجيل الخطأ في الكونسول فقط لتجنب إرباك المستخدم
        print(f"Basic Search Error: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# --- البحث العميق (Deep Search) ---
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
        
        wait = WebDriverWait(driver, 20)
        
        # 1. اختيار Electronic Work Permit Information
        try:
            select_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
            select = Select(select_element)
            select.select_by_visible_text("Electronic Work Permit Information")
            time.sleep(1)
        except:
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
        
        time.sleep(2)

        # 2. إدخال رقم البطاقة
        card_input = None
        try:
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
        else:
            return result_data

        # 3. فك الكابتشا
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
        time.sleep(2)

        # 4. الضغط على زر البحث
        try:
            search_btn = driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Search') or contains(text(), 'بحث')] | //input[@type='submit']")
            search_btn.click()
        except:
            driver.execute_script("document.forms[0].submit()")
            
        time.sleep(4)

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
        print(f
