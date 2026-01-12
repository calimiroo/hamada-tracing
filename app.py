import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Page Configuration ---
st.set_page_config(page_title="MOHRE Tracing System", layout="wide")

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'stop' not in st.session_state: st.session_state.stop = False

def sign_out():
    st.session_state.authenticated = False
    st.rerun()

# --- Login System ---
if not st.session_state.authenticated:
    st.subheader("🔑 Login System")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == "Hamada":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()
else:
    st.sidebar.button("🔴 Sign Out", on_click=sign_out)

# --- Enhanced Search Engine ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def scrape_data(passport, nationality, dob):
    driver = get_driver()
    if not driver: return "System Error"
    
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 20)
        
        # 1. Passport Input
        p_field = wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber")))
        p_field.send_keys(str(passport))
        
        # 2. Nationality Selection (Fixed Logic)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        search_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")))
        search_box.send_keys(str(nationality))
        time.sleep(2) # Necessary for the list to filter
        
        # Click the first matching result in the list
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items:
            driver.execute_script("arguments[0].click();", items[0])
        else:
            return "Nationality Not Found"
            
        # 3. DOB Injection (Fixed Logic)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        driver.execute_script(f"arguments[0].value = '{str(dob)}';", dob_field)
        
        # 4. Submit
        driver.find_element(By.ID, "btnSubmit").click()
        
        # 5. Wait for Result Table
        time.sleep(8)
        
        # 6. Extracting Real Data (Updated XPaths)
        def gv(id_val):
            try:
                # Find element by ID or XPath label
                element = driver.find_element(By.ID, id_val)
                val = element.text.strip()
                return val if val else "Not Found"
            except:
                try:
                    # Fallback to general span search
                    xpath = f"//*[contains(text(), '{id_val}')]/following-sibling::span"
                    return driver.find_element(By.XPATH, xpath).text.strip()
                except: return "N/A"

        # Check if search was successful by looking for Job Description
        job = gv("lblJobDescription") # Looking for the actual ID used in the portal
        if job == "N/A" or job == "":
            job = gv("Job Description") # Try text label

        if job == "N/A": return "No Data Found"

        return {
            "Job Description": job,
            "Card Number": gv("Card Number"),
            "Contract Start": gv("Contract Start"),
            "Contract End": gv("Contract End"),
            "Basic Salary": gv("Basic Salary"),
            "Total Salary": gv("Total Salary")
        }
    except Exception as e:
        return "Not Found"
    finally:
        driver.quit()

# --- User Interface ---
st.title("🛡️ HAMADA TRACING SYSTEM")

tab1, tab2 = st.tabs(["🔍 Individual Search", "📂 Batch Processing"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="p1")
    n_in = c2.text_input("Nationality", key="n1")
    d_in = c3.text_input("DOB (DD/MM/YYYY)", key="d1")
    
    if st.button("Start Search"):
        with st.spinner("Searching..."):
            res = scrape_data(p_in, n_in, d_in)
            if isinstance(res, dict):
                st.success("Success!")
                st.table(pd.DataFrame([res]))
            else:
                st.error(f"Result: {res}")

with tab2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
    if f:
        df_in = pd.read_excel(f)
        total = len(df_in)
        
        col1, col2 = st.columns([1, 4])
        if col1.button("▶️ Start"):
            st.session_state.stop = False
            results = []
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            t_box = m1.empty()
            r_box = m2.empty()
            s_box = m3.empty()
            
            p_bar = st.progress(0)
            t_spot = st.empty()
            start_time = time.time()
            success_count = 0

            for i, row in df_in.iterrows():
                if st.session_state.stop: break
                
                t_box.metric("⏳ Timer", f"{round(time.time()-start_time, 1)}s")
                r_box.metric("📊 Progress", f"{i+1} / {total}")
                s_box.metric("✅ Success", success_count)
                
                data = scrape_data(row[0], row[1], row[2])
                
                entry = {"Passport": row[0], "Nationality": row[1], "DOB": row[2], "Status": "Success" if isinstance(data, dict) else data}
                if isinstance(data, dict):
                    entry.update(data)
                    success_count += 1
                else:
                    for col in ["Job Description", "Card Number", "Contract Start", "Contract End", "Basic Salary", "Total Salary"]:
                        entry[col] = "N/A"
                
                results.append(entry)
                p_bar.progress((i+1)/total)
                t_spot.dataframe(pd.DataFrame(results))

            st.success("Task Finished!")
            st.download_button("Download CSV", pd.DataFrame(results).to_csv(index=False).encode('utf-8'), "Results.csv")
            
        if col2.button("🛑 Stop"):
            st.session_state.stop = True
