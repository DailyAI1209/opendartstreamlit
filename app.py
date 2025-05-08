import streamlit as st
import pandas as pd
from OpenDartReader import OpenDartReader
from datetime import datetime
from io import BytesIO

API_KEY = st.secrets["API_KEY"]
dart = OpenDartReader(API_KEY)

st.set_page_config(page_title="재무제표 챗봇", layout="centered")
st.title("📊 재무제표 조회 챗봇")

st.markdown("""
안녕하세요! 🧾  
원하는 **회사명**을 입력하면,  
DART에서 실시간으로 최근 재무제표 데이터를 가져올게요.
""")

# 사용자 입력 UI
company_name = st.text_input("회사명을 입력해주세요 (예: 삼성전자)", "삼성전자")
year_option = st.radio("연도 선택", ["최신 데이터(작년)", "직접 입력"])

if year_option == "직접 입력":
    year = st.text_input("조회할 연도 (예: 2022)", "2022")
else:
    year = datetime.today().year - 1

# 버튼 클릭 시 데이터 조회
if st.button("📥 재무제표 조회"):
    with st.spinner("📡 DART로부터 데이터를 가져오는 중입니다..."):
        try:
            # 회사 코드 찾기
            corp_code = dart.find_corp_code(company_name.strip())
            
            if corp_code is None:
                st.error(f"❌ '{company_name}'의 고유번호를 찾을 수 없습니다.")
            else:
                # 재무제표 가져오기
                df = dart.finstate(corp_code, int(year))
                
                if df is not None and not df.empty:
                    st.success(f"✅ {company_name}의 {year}년 재무제표입니다.")
                    
                    # 보여줄 데이터 선택 (현재 기간과 이전 기간 추가)
                    df_show = df[['sj_nm', 'account_nm', 'thstrm_amount', 'frmtrm_amount']]
                    st.dataframe(df_show, use_container_width=True)
                    
                    # CSV 다운로드 버튼
                    csv = df_show.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📤 CSV로 다운로드",
                        data=csv,
                        file_name=f"{company_name}_{year}_재무제표.csv",
                        mime='text/csv'
                    )
                    
                    # Excel 다운로드 버튼 추가
                    def to_excel(df):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='재무제표')
                        output.seek(0)
                        return output.getvalue()
                    
                    excel_data = to_excel(df_show)
                    st.download_button(
                        label="📂 엑셀로 다운로드",
                        data=excel_data,
                        file_name=f"{company_name}_{year}_재무제표.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning(f"⚠️ {company_name}의 {year}년 재무제표가 존재하지 않거나 공시되지 않았어요.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
