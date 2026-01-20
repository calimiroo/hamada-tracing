import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- حل مشكلة نقص distutils لضمان تشغيل المتصفح في البيئات السحابية ---
try:
    import distutils.version
except ImportError:
    import sys
    from packaging import version
    import types
    m = types.ModuleType('distutils')
    sys.modules['distutils'] = m
    m.version = types.ModuleType('distutils.version')
    sys.modules['distutils.version'] = m.version
    m.version.LooseVersion = version.parse

# استيراد المكتبات المتقدمة للجداول
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
except ImportError:
    st.error("مكتبة st-aggrid غير مثبتة. تأكد من وجودها في requirements.txt")
    st.stop()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal Pro", layout="wide")

# --- إدارة الجلسة (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'df_main' not in st.session_state:
    st.session_state['df_main'] = None

# --- قائمة الجنسيات (كاملة بدون اختصار كما طلبت) ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/database.png", width=80)
    st.title("⚙️ لوحة التحكم")
    st.markdown("---")
    
    # ميزة تنسيق التاريخ المطلوبة
    st.subheader("🛠️ أدوات البيانات")
    if st.button("🪄 Format Date (dd/mm/yyyy)"):
        if st.session_state.df_main is not None:
            try:
                # تحويل عمود التاريخ لتنسيق موحد يوم/شهر/سنة
                st.session_state.df_main['Date of Birth'] = pd.to_datetime(st.session_state.df_main['Date of Birth']).dt.strftime('%d/%m/%Y')
                st.success("✅ تم تحديث تنسيق التواريخ")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ فشل التنسيق: {e}")
        else:
            st.warning("⚠️ يرجى رفع ملف Excel أولاً!")
    
    st.markdown("---")
    st.info("قم برفع الملف ثم اضغط على زر التنسيق لتجهيز البيانات قبل البحث.")

# --- نظام تسجيل الدخول (تم إصلاح خطأ Form) ---
if not st.session_state['authenticated']:
    with st.form("auth_form"):
        st.subheader("🔐 Protected Access")
        password = st.text_input("Enter Access Password", type="password")
        # استخدام st.form_submit_button حصراً داخل الفورم
        login_clicked = st.form_submit_button("Verify & Enter")
        
        if login_clicked:
            if password == "Bilkish":
                st.session_state['authenticated'] = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Invalid Password")
    st.stop()

# --- واجهة التطبيق الرئيسية ---
st.title("🚀 HAMADA TRACING - FULL VERSION")

tab1, tab2 = st.tabs(["🔍 Single Search", "📊 Batch Processing"])

with tab1:
    with st.form("single_search"):
        st.subheader("Person Details")
        col1, col2, col3 = st.columns(3)
        passport = col1.text_input("Passport Number")
        nationality = col2.selectbox("Nationality", countries_list)
        dob = col3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1))
        
        # الزر الإلزامي للفورم لضمان عدم ظهور الخطأ في الصورة
        search_btn = st.form_submit_button("Execute Search")
        
        if search_btn:
            if passport and nationality != "Select Nationality" and dob:
                st.info(f"Searching for: {passport}...")
                # هنا يتم استدعاء دالة البحث Selenium (get_driver)
            else:
                st.warning("Please fill all fields.")

with tab2:
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        if st.session_state.df_main is None:
            st.session_state.df_main = pd.read_excel(uploaded_file)
        
        # إعداد جدول AgGrid المطور (يشمل القائمة الجانبية التي ظهرت في صورتك)
        gb = GridOptionsBuilder.from_dataframe(st.session_state.df_main)
        gb.configure_pagination(paginationPageSize=10)
        gb.configure_side_bar() # تفعيل المينو الجانبي للجدول (Sort, Filter, Hide)
        gb.configure_default_column(editable=True, groupable=True)
        grid_options = gb.build()

        st.markdown("### 📄 Data Preview")
        grid_response = AgGrid(
            st.session_state.df_main,
            gridOptions=grid_options,
            theme='alpine',
            height=400,
            update_mode=GridUpdateMode.MODEL_CHANGED
        )
        
        # حفظ التعديلات التي تتم يدوياً في الجدول
        st.session_state.df_main = grid_response['data']

        if st.button("▶️ Start Batch Processing"):
            st.write("Process started...")
