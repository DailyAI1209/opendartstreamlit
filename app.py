import streamlit as st
import OpenDartReader
import pandas as pd

# Streamlit Cloud secrets에서 API 키 가져오기
API_KEY = st.secrets["API_KEY"]
dart = OpenDartReader(API_KEY)

# 2. 페이지 기본 설정
st.set_page_config(page_title="재무제표 챗봇", layout="centered")
st.title("📊 재무제표 조회 챗봇")

st.markdown("""
안녕하세요! 🧾  
원하는 **회사명**과 **연도**를 입력하면,  
DART에서 실시간으로 재무제표 데이터를 가져올게요.
""")

# 3. 사용자 입력 UI
company_name = st.text_input("회사명을 입력해주세요 (예: 삼성전자)", "삼성전자")
year = st.text_input("조회할 연도 (예: 2022)", "2022")

# 4. 버튼 클릭 시 데이터 조회
if st.button("📥 재무제표 조회"):
    with st.spinner("📡 DART로부터 데이터를 가져오는 중입니다..."):
        try:
            df = dart.finstate(company_name.strip(), int(year))
            if df is not None and not df.empty:
                st.success(f"✅ {company_name}의 {year}년 재무제표입니다.")
                df_show = df[['sj_div', 'account_nm', 'thstrm_amount']]
                st.dataframe(df_show, use_container_width=True)
                
                # 다운로드 버튼
                csv = df_show.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📤 CSV로 다운로드",
                    data=csv,
                    file_name=f"{company_name}_{year}_재무제표.csv",
                    mime='text/csv'
                )
            else:
                st.warning(f"⚠️ {company_name}의 {year}년 재무제표가 존재하지 않거나 공시되지 않았어요.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
