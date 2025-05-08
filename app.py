import streamlit as st
import OpenDartReader
import pandas as pd
from datetime import datetime
from io import BytesIO

# ✅ Streamlit 기본 설정
st.set_page_config(page_title="재무제표 조회 앱", layout="centered")
st.title("📊 재무제표 조회 및 다운로드 앱")

st.markdown("회사명과 연도를 입력하면 재무제표를 불러와 보여드립니다.")

# ✅ Streamlit Cloud의 secrets에서 API 키 가져오기
api_key = st.secrets["API_KEY"]
dart = OpenDartReader(api_key)

# ✅ 사용자 입력
company_name = st.text_input("회사명을 입력하세요 (예: 삼성전자)", "삼성전자")

# 연도 선택 추가
current_year = datetime.today().year
year = st.selectbox("조회할 연도", 
                   options=list(range(current_year-5, current_year)),
                   index=0)

# ✅ 조회 버튼
if st.button("📥 재무제표 조회"):
    with st.spinner("📡 DART로부터 데이터를 가져오는 중입니다..."):
        try:
            # 회사명으로 직접 조회
            fs = dart.finstate(company_name, year)
            
            if fs is None or fs.empty:
                # 회사명으로 조회 실패 시 고유번호로 재시도
                corp_code = dart.find_corp_code(company_name)
                if corp_code is None:
                    st.error(f"❌ '{company_name}'의 고유번호를 찾을 수 없습니다.")
                else:
                    fs = dart.finstate(corp_code, year)
                    if fs is None or fs.empty:
                        st.warning(f"'{company_name}'의 {year}년도 재무제표를 찾을 수 없습니다.")
            
            if fs is not None and not fs.empty:
                output_df = fs[['sj_nm', 'account_nm', 'thstrm_amount', 'frmtrm_amount']]
                st.success(f"✅ '{company_name}'의 {year}년 재무제표를 불러왔습니다.")
                st.dataframe(output_df, use_container_width=True)

                # ✅ 엑셀 파일 다운로드 버튼
                def to_excel(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='재무제표')
                    output.seek(0)
                    return output.getvalue()

                excel_data = to_excel(output_df)

                st.download_button(
                    label="📂 엑셀로 다운로드",
                    data=excel_data,
                    file_name=f"{company_name}_{year}_재무제표.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
