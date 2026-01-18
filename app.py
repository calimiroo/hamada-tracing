# deep_search_addon.py
#
# وحدة البحث العميق (Deep Search) - نسخة محسّنة
# هذه الوحدة تُضاف كإضافة بسيطة دون تعديل الستايل الأصلي أو الوظائف الأساسية
# الخطأ المصحح: استبدال st.experimental_rerun() بـ st.rerun() (متوافق مع Streamlit >= 1.27)
#
# المتطلبات:
# - streamlit >= 1.27
# - pandas
# - selenium
# - undetected-chromedriver

import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- 1. تهيئة Selenium Driver ---

def get_selenium_driver() -> WebDriver:
    """
    Initializes or retrieves an undetected_chromedriver instance.
    Configured for Streamlit Cloud compatibility.
    """
    if 'selenium_driver' not in st.session_state:
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

# --- 2. منطق البحث العميق (Core Logic) ---

CAPTCHA_SOLVER_JS = """
    // يجب استبدال هذا الكود بكود JS الفعلي الذي يحل CAPTCHA
    var solution = '12345';
    document.getElementById('InputCaptcha').value = solution;
"""

def perform_deep_search_core(driver: WebDriver, card_number: str) -> dict | None:
    """
    Core deep search logic for a single card number.
    Returns extracted data dict or None on failure.
    """
    URL = "https://inquiry.mohre.gov.ae/"
    MAX_RETRIES = 3
    
    for attempt in range(MAX_RETRIES):
        try:
            driver.get(URL)
            wait = WebDriverWait(driver, 15)

            # Select service
            dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
            dropdown_button.click()
            
            search_input = wait.until(EC.presence_of_element_located((By.ID, "searchInput")))
            search_input.send_keys("معلومات تصريح العمل الإلكتروني")
            
            service_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='optionsList']/li[contains(text(), 'معلومات تصريح العمل الإلكتروني')]")))
            service_option.click()
            
            # Input card number
            input_data_field = wait.until(EC.presence_of_element_located((By.ID, "InputData")))
            input_data_field.send_keys(card_number)

            # Handle CAPTCHA
            captcha_field = wait.until(EC.presence_of_element_located((By.ID, "InputCaptcha")))
            driver.execute_script(CAPTCHA_SOLVER_JS)
            
            # Click search
            search_button = wait.until(EC.element_to_be_clickable((By.ID, "searchDataBtn")))
            search_button.click()

            # Wait for results
            results_container = wait.until(EC.presence_of_element_located((By.ID, "resultsContainerId")))
            
            # Extract data
            extracted_data = {
                "Company Name": results_container.find_element(By.ID, "companyNameId").text,
                "Company Code": results_container.find_element(By.ID, "companyCodeId").text,
                "Employee Name": results_container.find_element(By.ID, "employeeNameId").text,
                "Profession": results_container.find_element(By.ID, "professionId").text,
            }
            
            return extracted_data

        except TimeoutException:
            try:
                refresh_button = driver.find_element(By.ID, "refreshCaptchaBtn")
                refresh_button.click()
                time.sleep(2)
            except:
                pass
        except NoSuchElementException as e:
            st.error(f"Element not found: {e}")
            return None
        except Exception as e:
            st.error(f"Error during deep search: {e}")
            return None
            
    return None

# --- 3. وظائف التحكم (Control Functions) ---

def update_dataframe_with_deep_search(row_index: int, additional_data: dict):
    """Updates the DataFrame with deep search results."""
    if 'results_df' not in st.session_state:
        return False
        
    df = st.session_state.results_df
    
    # Add new columns if they don't exist
    for col in additional_data.keys():
        if col not in df.columns:
            df[col] = pd.NA
            
    # Update the row
    df.loc[row_index, additional_data.keys()] = additional_data.values()
    st.session_state.results_df = df
    return True

def perform_single_deep_search(row_index: int, card_number: str):
    """Performs a single deep search for one card number."""
    driver = get_selenium_driver()
    if driver is None:
        st.error("Failed to initialize Selenium driver.")
        return False

    with st.spinner(f"Performing Deep Search for {card_number}..."):
        additional_data = perform_deep_search_core(driver, card_number)
        
        if additional_data:
            update_dataframe_with_deep_search(row_index, additional_data)
            st.success(f"Deep Search completed for {card_number}!")
            return True
        else:
            st.error(f"Deep Search failed for {card_number}.")
            return False

def perform_batch_deep_search():
    """Performs batch deep search for all unenriched 'Found' records."""
    df = st.session_state.results_df
    
    # Ensure new columns exist
    new_cols = ['Company Name', 'Company Code', 'Employee Name', 'Profession']
    for col in new_cols:
        if col not in df.columns:
            df[col] = pd.NA
            
    # Find unenriched 'Found' rows
    found_rows = df[df['Status'] == 'Found']
    unenriched_rows = found_rows[pd.isna(found_rows['Company Name'])]
    
    if unenriched_rows.empty:
        st.info("All 'Found' records are already enriched.")
        return

    total_tasks = len(unenriched_rows)
    progress_bar = st.progress(0, text=f"Batch Deep Search: 0 of {total_tasks} completed.")
    
    driver = get_selenium_driver()
    if driver is None:
        st.error("Failed to initialize Selenium driver.")
        return

    for i, (index, row) in enumerate(unenriched_rows.iterrows()):
        card_number = row['Card Number']
        
        progress_bar.progress((i + 1) / total_tasks, text=f"Processing {card_number} ({i + 1} of {total_tasks})...")
        
        additional_data = perform_deep_search_core(driver, card_number)
        
        if additional_data:
            update_dataframe_with_deep_search(index, additional_data)
            st.success(f"Enriched {card_number}")
        else:
            st.warning(f"Failed to enrich {card_number}")

    progress_bar.empty()
    st.success("Batch Deep Search completed!")

# --- 4. واجهة المستخدم (UI Functions) ---

def show_deep_search_buttons(df: pd.DataFrame):
    """
    Shows Deep Search buttons ONLY after the first phase is complete.
    This function should be called AFTER displaying the main results table.
    """
    # Check if first phase is complete (i.e., results_df has data)
    if df is None or df.empty:
        return
    
    # Ensure new columns exist
    new_cols = ['Company Name', 'Company Code', 'Employee Name', 'Profession']
    for col in new_cols:
        if col not in df.columns:
            df[col] = pd.NA
    
    # Find 'Found' rows
    found_rows = df[df['Status'] == 'Found']
    
    if found_rows.empty:
        return
    
    # Display Deep Search section
    st.markdown("---")
    st.subheader("Deep Search - Enrich Data from MOHRE Portal")
    
    # Batch search button
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Automatically enrich all 'Found' records:")
    with col2:
        if st.button("Start Batch Deep Search", key="batch_deep_search_btn"):
            perform_batch_deep_search()
            st.rerun()  # Fixed: using st.rerun() instead of st.experimental_rerun()
    
    # Single row search buttons
    st.markdown("---")
    st.caption("Or enrich individual records:")
    
    for index, row in found_rows.iterrows():
        card_number = row['Card Number']
        
        # Check if already enriched
        if pd.notna(row['Company Name']):
            st.markdown(f"✅ **{card_number}**: Already enriched")
            continue
        
        # Show button for unenriched rows
        if st.button(
            f"Deep Search: {card_number}",
            key=f"deep_search_btn_{index}"
        ):
            perform_single_deep_search(index, card_number)
            st.rerun()  # Fixed: using st.rerun() instead of st.experimental_rerun()
