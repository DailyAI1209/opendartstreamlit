import streamlit as st
import pandas as pd
from OpenDartReader import OpenDartReader
from io import BytesIO

API_KEY = st.secrets["API_KEY"]
dart = OpenDartReader(API_KEY)

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
            # 첫 번째 코드와 동일한 방식으로 재무제표 가져오기
            df = dart.finstate(company_name.strip(), int(year))
            
            if df is not None and not df.empty:
                st.success(f"✅ {company_name}의 {year}년 재무제표입니다.")
                
                # 표시할 컬럼 선택 (두 번째 코드의 컬럼 구성 적용)
                if 'sj_nm' in df.columns and 'account_nm' in df.columns and 'thstrm_amount' in df.columns:
                    # 두 번째 코드의 방식대로 컬럼 선택
                    if 'frmtrm_amount' in df.columns:
                        df_show = df[['sj_nm', 'account_nm', 'thstrm_amount', 'frmtrm_amount']]
                    else:
                        df_show = df[['sj_nm', 'account_nm', 'thstrm_amount']]
                else:
                    # 첫 번째 코드의 방식대로 컬럼 선택
                    available_columns = ['account_nm', 'thstrm_amount']
                    if 'sj_div' in df.columns:
                        available_columns.insert(0, 'sj_div')
                    elif 'sj_nm' in df.columns:
                        available_columns.insert(0, 'sj_nm')
                    if 'frmtrm_amount' in df.columns:
                        available_columns.append('frmtrm_amount')
                    df_show = df[available_columns]
                
                st.dataframe(df_show, use_container_width=True)
                
                # Excel 다운로드 기능 추가 (두 번째 코드의 엑셀 다운로드 방식)
                def to_excel(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='재무제표')
                    output.seek(0)  # 버퍼의 포인터를 처음으로 되돌림
                    return output.getvalue()
                
                excel_data = to_excel(df_show)
                
                st.download_button(
                    label="📂 엑셀로 다운로드",
                    data=excel_data,
                    file_name=f"{company_name}_{year}_재무제표.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # CSV 다운로드 옵션도 유지
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
