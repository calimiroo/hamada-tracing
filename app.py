# deep_search_module_v2.py
#
# هذا الملف يحتوي على الوظائف الإضافية لوحدة "Deep Search"
# تم تحديثه لدعم البحث الفردي (Single Search) والبحث الدفعي (Batch Processing).
#
# المتطلبات:
# 1. يجب تثبيت الحزم التالية: streamlit, pandas, selenium, undetected-chromedriver
# 2. يجب أن يكون لديك دالة get_selenium_driver() معدة مسبقاً في تطبيقك الحالي.

import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- 1. إعدادات وتكوين Selenium (يجب مراجعتها وتعديلها لتناسب بيئتك) ---

# ملاحظة: يجب أن تكون هذه الدالة موجودة بالفعل في تطبيقك الحالي.
def get_selenium_driver() -> WebDriver:
    """
    Initializes or retrieves an undetected_chromedriver instance.
    Configured for Streamlit Cloud compatibility.
    """
    if 'selenium_driver' not in st.session_state:
        st.info("Initializing new Selenium driver for Deep Search...")
        
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            driver = uc.Chrome(options=options)
            st.session_state['selenium_driver'] = driver
        except Exception as e:
            st.error(f"Failed to initialize Selenium driver: {e}")
            return None
            
    return st.session_state['selenium_driver']

# --- 2. منطق الأتمتة (محرك البحث العميق) ---

# **هام:** يجب استبدال هذا المتغير بكود JavaScript الفعلي الذي يحل CAPTCHA.
# هذا مجرد مثال توضيحي لكيفية حقن القيمة في حقل الإدخال.
CAPTCHA_SOLVER_JS = """
    // يجب أن يتم استبدال هذا الكود بكود JS الفعلي الذي يحل CAPTCHA
    var solution = '12345'; // **استبدل هذا بالحل الفعلي**
    document.getElementById('InputCaptcha').value = solution;
"""

def perform_deep_search_core(driver: WebDriver, card_number: str) -> dict | None:
    """
    The core logic for a single deep search operation.
    Returns extracted data or None on failure.
    """
    URL = "https://inquiry.mohre.gov.ae/"
    MAX_RETRIES = 3
    
    for attempt in range(MAX_RETRIES):
        try:
            # 1. Navigate to the URL
            driver.get(URL)
            wait = WebDriverWait(driver, 15)

            # 2. Select the service: "Electronic Work Permit Information"
            dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
            dropdown_button.click()
            
            search_input = wait.until(EC.presence_of_element_located((By.ID, "searchInput")))
            search_input.send_keys("معلومات تصريح العمل الإلكتروني")
            
            service_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='optionsList']/li[contains(text(), 'معلومات تصريح العمل الإلكتروني')]")))
            service_option.click()
            
            # 3. Input Card Number
            input_data_field = wait.until(EC.presence_of_element_located((By.ID, "InputData")))
            input_data_field.send_keys(card_number)

            # 4. Handle CAPTCHA using JavaScript snippet
            captcha_field = wait.until(EC.presence_of_element_located((By.ID, "InputCaptcha")))
            driver.execute_script(CAPTCHA_SOLVER_JS)
            
            # 5. Click Search
            search_button = wait.until(EC.element_to_be_clickable((By.ID, "searchDataBtn")))
            search_button.click()

            # 6. Wait for results to load
            # **يجب تعديل هذا المحدد (Selector) ليتناسب مع صفحة النتائج الفعلية**
            results_container = wait.until(EC.presence_of_element_located((By.ID, "resultsContainerId")))
            
            # 7. Extract Data
            # **يجب تعديل محددات الاستخلاص (Selectors) لصفحة النتائج الفعلية**
            extracted_data = {
                "Company Name": results_container.find_element(By.ID, "companyNameId").text,
                "Company Code": results_container.find_element(By.ID, "companyCodeId").text,
                "Employee Name": results_container.find_element(By.ID, "employeeNameId").text,
                "Profession": results_container.find_element(By.ID, "professionId").text,
            }
            
            return extracted_data

        except TimeoutException:
            # محاولة تحديث CAPTCHA قبل المحاولة التالية
            try:
                refresh_button = driver.find_element(By.ID, "refreshCaptchaBtn")
                refresh_button.click()
                time.sleep(2)
            except:
                pass
            st.warning(f"Deep Search: Timeout for {card_number} on attempt {attempt + 1}.")
        except NoSuchElementException as e:
            st.error(f"Deep Search: Element not found for {card_number}. Error: {e}")
            return None
        except Exception as e:
            st.error(f"Deep Search: Unexpected error for {card_number}: {e}")
            return None
            
    return None

# --- 3. منطق التحكم في Streamlit (UI & Session State) ---

def update_dataframe(row_index: int, additional_data: dict):
    """Updates the DataFrame in session state with new data."""
    if 'results_df' in st.session_state:
        df = st.session_state.results_df
        
        # إضافة الأعمدة الجديدة إذا لم تكن موجودة
        for col in additional_data.keys():
            if col not in df.columns:
                df[col] = pd.NA
                
        # تحديث الصف المحدد
        df.loc[row_index, additional_data.keys()] = additional_data.values()
        st.session_state.results_df = df
        return True
    return False

def handle_single_deep_search(row_index: int, card_number: str):
    """
    Handles the 'Deep Search' button click event for a single row.
    This function is called by the button click and triggers a Streamlit rerun.
    """
    # Safeguard: Prevent concurrent searches
    if st.session_state.get('deep_search_locked', False):
        st.warning("A Deep Search is already in progress. Please wait.")
        return

    st.session_state['deep_search_locked'] = True
    st.session_state['single_search_index'] = row_index
    
    # يتم تشغيل العملية الفعلية في الدالة الرئيسية بعد إعادة التشغيل
    st.experimental_rerun()

def run_single_deep_search():
    """Executes the single deep search logic after a button click triggers a rerun."""
    row_index = st.session_state.get('single_search_index')
    if row_index is None:
        return

    df = st.session_state.results_df
    card_number = df.loc[row_index, 'Card Number']
    
    with st.spinner(f"Performing Deep Search for {card_number}..."):
        driver = get_selenium_driver() 
        if driver is None:
            st.session_state['deep_search_locked'] = False
            st.session_state['single_search_index'] = None
            return

        additional_data = perform_deep_search_core(driver, card_number)
        
        if additional_data:
            update_dataframe(row_index, additional_data)
            st.success(f"Deep Search completed successfully for {card_number}!")
        else:
            st.error(f"Deep Search failed or returned no data for {card_number}.")
            
    st.session_state['deep_search_locked'] = False
    st.session_state['single_search_index'] = None
    st.experimental_rerun() # إعادة تشغيل أخيرة لتحديث الواجهة

def start_batch_deep_search():
    """
    Initiates the automated batch deep search for all 'Found' records 
    that have not been enriched yet.
    """
    if st.session_state.get('deep_search_locked', False):
        st.warning("A Deep Search is already in progress. Please wait.")
        return

    st.session_state['deep_search_locked'] = True
    st.session_state['batch_search_active'] = True
    
    # يتم تشغيل العملية الفعلية في الدالة الرئيسية بعد إعادة التشغيل
    st.experimental_rerun()

def run_batch_deep_search():
    """Executes the batch deep search logic after a button click triggers a rerun."""
    if not st.session_state.get('batch_search_active', False):
        return

    df = st.session_state.results_df
    
    # تحديد الصفوف التي تحتاج إلى بحث عميق
    new_cols = ['Company Name', 'Company Code', 'Employee Name', 'Profession']
    for col in new_cols:
        if col not in df.columns:
            df[col] = pd.NA
            
    found_rows = df[df['Status'] == 'Found']
    
    # تحديد الصفوف غير المثرية
    unenriched_rows = found_rows[pd.isna(found_rows['Company Name'])]
    
    if unenriched_rows.empty:
        st.info("Batch Deep Search: All 'Found' records are already enriched.")
        st.session_state['deep_search_locked'] = False
        st.session_state['batch_search_active'] = False
        st.experimental_rerun()
        return

    total_tasks = len(unenriched_rows)
    progress_bar = st.progress(0, text=f"Batch Deep Search: 0 of {total_tasks} completed.")
    
    driver = get_selenium_driver()
    if driver is None:
        st.session_state['deep_search_locked'] = False
        st.session_state['batch_search_active'] = False
        return

    for i, (index, row) in enumerate(unenriched_rows.iterrows()):
        card_number = row['Card Number']
        
        progress_bar.progress((i + 1) / total_tasks, text=f"Batch Deep Search: Processing {card_number} ({i + 1} of {total_tasks})...")
        
        additional_data = perform_deep_search_core(driver, card_number)
        
        if additional_data:
            update_dataframe(index, additional_data)
            st.success(f"Enriched {card_number}")
        else:
            st.warning(f"Failed to enrich {card_number}")
            
        # تحديث الواجهة مباشرة بعد كل صف (لتحقيق "live, row by row")
        # هذا يتطلب إعادة تشغيل Streamlit، وهو غير فعال في حلقة، لذا سنعتمد على تحديث placeholder
        # في بيئة Streamlit الحقيقية، يجب استخدام st.empty() و st.dataframe() لتحديث الجدول في مكانه.
        # هنا، سنعتمد على تحديث شريط التقدم والرسائل.

    progress_bar.empty()
    st.success("Batch Deep Search completed!")
    st.session_state['deep_search_locked'] = False
    st.session_state['batch_search_active'] = False
    st.experimental_rerun() # إعادة تشغيل أخيرة لتحديث الجدول بالكامل

def display_results_table(df: pd.DataFrame):
    """
    Renders the results DataFrame in Streamlit, adding the 'Deep Search' button 
    for 'Found' rows and the Batch Search button.
    """
    # 1. Ensure new columns exist
    new_cols = ['Company Name', 'Company Code', 'Employee Name', 'Profession']
    for col in new_cols:
        if col not in df.columns:
            df[col] = pd.NA

    # 2. Display the table
    st.dataframe(df, use_container_width=True)
    
    # 3. Add Deep Search buttons
    st.markdown("---")
    st.subheader("Deep Search Actions")
    
    # زر البحث الدفعي (Batch Search)
    if st.button(
        "Start Batch Deep Search (Enrich All Found)",
        key="batch_deep_search_btn",
        disabled=st.session_state.get('deep_search_locked', False)
    ):
        start_batch_deep_search()

    st.markdown("---")
    st.caption("Single Row Deep Search:")
    
    found_rows = df[df['Status'] == 'Found']
    
    if found_rows.empty:
        st.info("No 'Found' records available for Deep Search.")
        return

    for index, row in found_rows.iterrows():
        card_number = row['Card Number']
        
        # التحقق مما إذا كان الصف قد تم إثراؤه بالفعل
        if pd.notna(row['Company Name']):
            st.markdown(f"✅ **{card_number}**: Data already enriched.")
            continue
            
        # عرض الزر للبحث الفردي
        if st.button(
            f"Deep Search: {card_number}", 
            key=f"single_deep_search_btn_{index}",
            disabled=st.session_state.get('deep_search_locked', False)
        ):
            handle_single_deep_search(index, card_number)

# --- 4. مثال على الاستخدام (للتجربة) ---

if __name__ == '__main__':
    st.title("Deep Search Module Integration Example (v2)")
    
    # تهيئة DataFrame في session_state إذا لم يكن موجوداً
    if 'results_df' not in st.session_state:
        st.session_state.results_df = pd.DataFrame({
            'Transaction Number': [1001, 1002, 1003, 1004, 1005],
            'Card Number': ['9876543210', '1234567890', '1122334455', '9988776655', '5544332211'],
            'Status': ['Found', 'Not Found', 'Found', 'Found', 'Found'],
            'Original Data': ['A', 'B', 'C', 'D', 'E']
        })
        
    # تشغيل منطق البحث الفردي أو الدفعي إذا تم تفعيله
    if st.session_state.get('single_search_index') is not None:
        run_single_deep_search()
    elif st.session_state.get('batch_search_active', False):
        run_batch_deep_search()
        
    # عرض الجدول والأزرار
    display_results_table(st.session_state.results_df)

    st.markdown("---")
    st.caption("Note: This is a simulation. The actual Selenium search will run when you click the button, but data extraction and CAPTCHA handling require correct selectors and a working CAPTCHA solver.")
    
    # زر لتنظيف الجلسة
    if st.button("Reset Data"):
        if 'results_df' in st.session_state:
            del st.session_state.results_df
        if 'selenium_driver' in st.session_state:
            st.session_state['selenium_driver'].quit()
            del st.session_state['selenium_driver']
        st.experimental_rerun()
