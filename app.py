import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from datetime import datetime
import os
import requests  # for translation via API
from st_aggrid import AgGrid, GridOptionsBuilder  # للجدول مع pagination

# All countries list (alphabetical, full list)
countries = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia",
    "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)",
    "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea",
    "Estonia", "Eswatini (fmr. \"Swaziland\")", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany",
    "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan",
    "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
    "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania",
    "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)",
    "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia",
    "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore",
    "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
    "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America",
    "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

# Set page config
st.set_page_config(page_title="MOHRE Contract Extractor", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# Password protection
password = st.text_input("Enter Password", type="password")
if password != "Bilkish":
    st.error("Incorrect Password")
    st.stop()

# Driver setup
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=en-US')
    return uc.Chrome(options=options)

# Translation function using free API (e.g., MyMemory)
def translate_text(text, from_lang='ar', to_lang='en'):
    if not text or text == 'Not Found':
        return text
    url = f"https://api.mymemory.translated.net/get?q={text}&langpair={from_lang}|{to_lang}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['responseData']['translatedText']
    return text  # Fallback if API fails

# Extraction function
def extract_single(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(3)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(3)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items:
            items[0].click()
        time.sleep(2)
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        time.sleep(1)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(12)
        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except:
                return 'Not Found'
        contract_type = get_value("Contract Type")
        job_description = get_value("Job Description")
        # Translate from Arabic to English
        contract_type_en = translate_text(contract_type)
        job_description_en = translate_text(job_description)
        result = {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Card Number": get_value("Card Number"),
            "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"),
            "Contract Type": contract_type_en,
            "Contract Start": get_value("Contract Start"),
            "Contract End": get_value("Contract End"),
            "Job Description": job_description_en,
            "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"),
            "Allowance Residence": get_value("Allowance Residence"),
            "Allowance Transport": get_value("Allowance Transport"),
            "Allowance Other 1": get_value("Allowance Other 1"),
            "Allowance Other 2": get_value("Allowance Other 2"),
            "Allowance Other 3": get_value("Allowance Other 3"),
            "Allowance Other 4": get_value("Allowance Other 4"),
        }
        return result
    except Exception as e:
        return {"Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str, "Error": str(e)}
    finally:
        driver.quit()

# Tabs
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])
with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    with col1:
        passport = st.text_input("Passport Number")
    with col2:
        nationality = st.selectbox("Nationality", countries, index=countries.index("Egypt") if "Egypt" in countries else 0)
    with col3:
        dob = st.date_input("Date of Birth", datetime(1990, 1, 1))
    dob_str = dob.strftime("%d/%m/%Y")
    if st.button("Search"):
        if passport:
            with st.spinner("Searching..."):
                result = extract_single(passport, nationality, dob_str)
            st.success("Done!")
            st.dataframe(pd.DataFrame([result]), use_container_width=True)
        else:
            st.error("Enter Passport Number")
with tab2:
    st.subheader("Upload Excel for Batch Search")
    uploaded_file = st.file_uploader("Upload data.xlsx", type=["xlsx"])
    if uploaded_file:
        # قراءة الإكسل بدون dtype محدد، ثم تحويل Date of Birth إلى string وإعادة تنسيق
        df = pd.read_excel(uploaded_file)
        
        # إعادة تنسيق Date of Birth إذا كان datetime أو string
        if 'Date of Birth' in df.columns:
            df['Date of Birth'] = df['Date of Birth'].apply(lambda x: pd.to_datetime(x, dayfirst=True, errors='coerce').strftime('%d/%m/%Y') if pd.notnull(x) else 'Not Found')
        
        # عرض الpreview الكامل مع pagination باستخدام AgGrid (10 rows per page)
        st.write("Uploaded File Preview (Full with Pagination):")
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)  # 10 rows per page
        gb.configure_side_bar()  # يضيف filters وcolumns
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options, height=400, use_container_width=True)
        
        if st.button("Start Batch Search"):
            start_time = time.time()  # بداية قياس الوقت
            progress_bar = st.progress(0)
            status_text = st.empty()
            found_count_text = st.empty()  # عنصر لعرض عدد النتائج المكتشفة
            time_text = st.empty()  # عنصر جديد لعرض الوقت الممضي
            results = []
            found_count = 0  # عداد النتائج الناجحة
            for i, row in df.iterrows():
                passport = str(row.get('Passport Number', '')).strip()
                nationality = str(row.get('Nationality', 'Egypt')).strip()
                original_dob = row.get('Date of Birth', '')
                dob_str = original_dob if original_dob != 'Not Found' else ''
                status_text.text(f"Searching: {passport} ({i+1}/{len(df)})")
                result = extract_single(passport, nationality, dob_str)
                results.append(result)
                # زد العداد إذا كانت النتيجة ناجحة (مثلاً إذا وجد Card Number)
                if result.get('Card Number', 'Not Found') != 'Not Found':
                    found_count += 1
                found_count_text.text(f"Found so far: {found_count}")
                
                # حساب وعرض الوقت الممضي
                elapsed_time = time.time() - start_time
                time_text.text(f"Elapsed time: {elapsed_time:.2f} seconds")
                
                progress_bar.progress((i + 1) / len(df))
            result_df = pd.DataFrame(results)
            total_time = time.time() - start_time  # الوقت الإجمالي
            st.success("Batch Search Complete!")
            st.write(f"Total search time: {total_time:.2f} seconds")  # عرض الوقت الإجمالي في النهاية
            st.dataframe(result_df, use_container_width=True, height=800)
            # Download
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results as CSV", csv, "contract_results.csv", "text/csv")
st.markdown("---")
st.caption("Developed by Grok - All in English")
