import streamlit as st
import OpenDartReader
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# ✅ DART API 키 설정 (환경 변수에서 가져오기)
# Streamlit Cloud에서는 Settings > Secrets에서 DART_API_KEY 환경 변수를 설정해야 합니다
api_key = st.secrets.get("DART_API_KEY", "")

# API 키가 없는 경우 입력 필드 제공
if not api_key:
    api_key = st.text_input("DART API 키를 입력하세요", type="password")
    if not api_key:
        st.warning("DART API 키가 필요합니다. API 키를 입력하거나 Streamlit Cloud의 Secrets에 'DART_API_KEY'를 설정하세요.")
        st.stop()

# OpenDartReader 초기화
dart = OpenDartReader(api_key)

# ✅ Streamlit 기본 설정
st.set_page_config(page_title="재무제표 조회 앱", layout="centered")
st.title("📊 재무제표 조회 및 다운로드 앱")

st.markdown("회사명을 입력하면 최근 연도의 재무제표를 불러와 보여드릴게요.")

# ✅ 사용자 입력
company_name = st.text_input("회사명을 입력하세요 (예: 삼성전자)", "삼성전자")

# 연도 선택 옵션 추가 (선택사항)
current_year = datetime.today().year
year = st.selectbox("조회할 연도를 선택하세요", range(current_year-5, current_year), index=1)

# ✅ 조회 버튼
if st.button("📥 재무제표 조회 및 다운로드"):
    with st.spinner(f"'{company_name}'의 재무제표를 조회 중입니다..."):
        corp_code = dart.find_corp_code(company_name)

        if corp_code is None:
            st.error(f"❌ '{company_name}'의 고유번호를 찾을 수 없습니다.")
        else:
            try:
                fs = dart.finstate(corp_code, year)

                if fs is None or fs.empty:
                    st.warning(f"'{company_name}'의 {year}년도 재무제표를 찾을 수 없습니다.")
                else:
                    output_df = fs[['sj_nm', 'account_nm', 'thstrm_amount', 'frmtrm_amount']]
                    st.success(f"✅ '{company_name}'의 {year}년 재무제표를 불러왔습니다.")
                    
                    # 재무제표 종류별로 탭 나누기
                    unique_statements = output_df['sj_nm'].unique()
                    tabs = st.tabs(unique_statements)
                    
                    for i, statement_type in enumerate(unique_statements):
                        with tabs[i]:
                            filtered_df = output_df[output_df['sj_nm'] == statement_type]
                            st.dataframe(filtered_df, use_container_width=True)
                    
                    # ✅ 엑셀 파일 버퍼로 저장
                    def to_excel(df):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            # 각 재무제표 유형별로 시트 생성
                            for statement_type in unique_statements:
                                sheet_df = df[df['sj_nm'] == statement_type]
                                sheet_df.to_excel(writer, index=False, sheet_name=statement_type[:31])  # 시트명 31자 제한
                        output.seek(0)  # 버퍼의 포인터를 처음으로 되돌림
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

# 푸터 추가
st.markdown("---")
st.markdown("### 사용 방법")
st.markdown("""
1. 회사명을 입력하세요 (예: 삼성전자, SK하이닉스 등)
2. 조회할 연도를 선택하세요
3. '재무제표 조회 및 다운로드' 버튼을 클릭하세요
4. 재무제표 데이터를 확인하고 필요시 엑셀로 다운로드하세요
""")
st.markdown("---")
st.markdown("OpenDartReader와 Streamlit으로 제작된 재무제표 조회 앱입니다.")
