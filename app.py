import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from st_aggrid import AgGrid, GridOptionsBuilder

# دالة المتصفح (معدلة لتجنب OSError)
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # استخدام مسار مؤقت فريد لكل تشغيل
    options.add_argument(f"--user-data-dir=/tmp/chrome_user_{int(time.time())}")
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

# واجهة الجدول مع القائمة المنسدلة (Menu) المطلوبة
uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # إعداد خيارات الجدول (AgGrid) لتمكين القائمة الجانبية والمنسدلة
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_side_bar() # لتفعيل القائمة التي تظهر في صورتك
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_default_column(editable=True, groupable=True)
    grid_opt = gb.build()

    # زر تنسيق التاريخ (يظهر بشكل أنيق فوق الجدول)
    if st.button("🪄 Format Date (dd/mm/yyyy)"):
        try:
            df['Date of Birth'] = pd.to_datetime(df['Date of Birth']).dt.strftime('%d/%m/%Y')
            st.success("تم تنسيق التاريخ بنجاح!")
            st.rerun()
        except:
            st.error("تأكد من وجود عمود Date of Birth")

    # عرض الجدول الاحترافي
    AgGrid(df, gridOptions=grid_opt, theme='alpine', height=400)
