import streamlit as st
import pandas as pd
import time
import os
import requests
from datetime import datetime

# محاولة استيراد AgGrid مع معالجة تعليق التثبيت
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
except ImportError:
    st.error("السيرفر لا يزال يقوم بتثبيت المكتبات، يرجى الانتظار دقيقة وعمل تحديث (Refresh) للصفحة.")
    st.stop()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

st.set_page_config(page_title="MOHRE Stable Pro", layout="wide")

# القائمة الجانبية (Sidebar) كما في طلبك
with st.sidebar:
    st.title("⚙️ خيارات الجدول")
    if st.button("🪄 تنسيق التاريخ (dd/mm/yyyy)"):
        if 'df_main' in st.session_state:
            try:
                st.session_state.df_main['Date of Birth'] = pd.to_datetime(st.session_state.df_main['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("تم التنسيق بنجاح!")
                st.rerun()
            except: st.error("تأكد من وجود عمود Date of Birth")
    st.markdown("---")

st.title("HAMADA TRACING SITE - STABLE")

# الحماية
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Password", type="password")
    if st.button("Login") and pwd == "Bilkish":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# دالة المتصفح (تعالج مشكلة OSError 24 عن طريق تنظيف المسارات)
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # إنشاء مسار مؤقت فريد لتحرير الملفات المفتوحة
    options.add_argument(f"--user-data-dir=/tmp/chrome_{int(time.time())}")
    try:
        return uc.Chrome(options=options, headless=True, use_subprocess=False)
    except Exception as e:
        st.error(f"خطأ في تشغيل المتصفح: {e}")
        return None

# واجهة الجدول المطور
uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
if uploaded:
    if 'df_main' not in st.session_state:
        st.session_state.df_main = pd.read_excel(uploaded)
    
    # إعدادات AgGrid لتفعيل المينو المنسدل
    gb = GridOptionsBuilder.from_dataframe(st.session_state.df_main)
    gb.configure_pagination(paginationPageSize=10)
    gb.configure_side_bar() # تفعيل القائمة الجانبية داخل الجدول
    gb.configure_default_column(editable=True, filter=True, groupable=True)
    grid_opt = gb.build()

    st.info("💡 اضغط كليك يمين داخل الجدول لرؤية الخيارات.")
    AgGrid(st.session_state.df_main, gridOptions=grid_opt, theme='alpine', height=400)

    if st.button("🚀 بدء البحث"):
        driver = get_driver()
        if driver:
            # هنا تضع منطق البحث الخاص بك...
            st.success("بدأ البحث...")
            driver.quit()
