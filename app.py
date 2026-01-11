import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import io

# إعداد الصفحة
st.set_page_config(page_title="Test-1 Laboratory", layout="wide")

# --- نظام تسجيل الدخول المحسن ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("🚀 Lab Access Control")
        pwd_input = st.text_input("Enter Access Key", type="password")
        if st.form_submit_button("Launch Lab"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Access Denied")
    st.stop()

# --- دالة الاستعلام الثانية (Inquiry Service) ---
@st.dialog("تفاصيل بطاقة العمل")
def show_inquiry_details(card_number):
    st.write(f"🔄 جاري الاتصال بنظام الاستعلامات للبطاقة: {card_number}")
    st.warning("يرجى الانتظار حتى تظهر صورة التحقق...")
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options, use_subprocess=False)
        
        # 1. الدخول لموقع الاستعلامات
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(3)
        
        # 2. اختيار Electronic Work Permit Information
        dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlService")))
        dropdown.click()
        time.sleep(1)
        # البحث عن الخيار المطلوب في القائمة
        driver.find_element(By.XPATH, "//option[contains(text(), 'Electronic Work Permit Information')]").click()
        time.sleep(2)
        
        # 3. إدخال رقم البطاقة في Transaction No
        driver.find_element(By.ID, "txtTransactionNo").send_keys(card_number)
        
        # 4. طلب كود الصورة من المستخدم
        captcha_img = driver.find_element(By.ID, "imgCaptcha")
        # في بيئة Streamlit السحابية، سنحتاج لعرض الصورة للمستخدم
        st.image(captcha_img.screenshot_as_png, caption="أدخل الكود الظاهر في الصورة")
        
        captcha_input = st.text_input("Verification Code", key="cap_input")
        if st.button("تأكيد واستخراج"):
            if captcha_input:
                driver.find_element(By.ID, "txtCaptcha").send_keys(captcha_input)
                driver.find_element(By.ID, "btnSearch").click()
                time.sleep(5)
                
                # 5. سحب النتائج
                res_data = {
                    "Est Name": driver.find_element(By.ID, "lblEstNameEn").text,
                    "Company Code": driver.find_element(By.ID, "lblEstNo").text,
                    "Person Name": driver.find_element(By.ID, "lblWorkerNameEn").text
                }
                
                st.success("✅ تم استخراج البيانات بنجاح")
                st.json(res_data) # عرض النتائج بشكل منظم
    except Exception as e:
        st.error(f"حدث خطأ أثناء الاستخراج: {str(e)}")
    finally:
        if driver: driver.quit()

# --- دالة البحث الأساسية (نفس الكود السابق مع ربط البطاقة) ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def extract_primary_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(5)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(2)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        time.sleep(1)
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)
        
        def get_v(label):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following::span[1]").text.strip()
            except: return "N/A"

        return {
            "Passport": passport,
            "Card Number": get_v("Card Number"),
            "Job": get_v("Job Description"),
            "Basic": get_v("Basic Salary"),
            "Total": get_v("Total Salary")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch Preview"])

with tab1:
    st.subheader("الاستعلام الأحادي")
    c1, c2, c3 = st.columns(3)
    p = c1.text_input("Passport")
    n = c2.selectbox("Nationality", ["Egypt", "India", "Pakistan"])
    d = c3.date_input("DOB", value=None, min_value=datetime(1900, 1, 1))

    if st.button("Search"):
        with st.spinner("Searching..."):
            res = extract_primary_data(p, n, d.strftime("%d/%m/%Y"))
            if res:
                st.table(pd.DataFrame([res]))
                # زر إضافي لفتح الاستعلام الثاني
                if res["Card Number"] != "N/A":
                    if st.button(f"🔎 استعلام عن الشركة برقم: {res['Card Number']}"):
                        show_inquiry_details(res["Card Number"])

with tab2:
    st.subheader("Batch Process")
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        df = pd.read_excel(up)
        st.dataframe(df) # معاينة بصفحات
        if st.button("Start Processing"):
            # منطق الـ Batch هنا...
            pass
