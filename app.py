import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# 패키지 설치 확인 및 설치
try:
    import OpenDartReader
except ImportError:
    st.error("OpenDartReader 패키지를 설치하는 중입니다. 잠시만 기다려주세요...")
    import subprocess
    subprocess.check_call(["pip", "install", "opendartreader"])
    import OpenDartReader
    st.experimental_rerun()

# ✅ DART API 키 설정 (Streamlit 시크릿에서 가져오기)
try:
    api_key = st.secrets["DART_API_KEY"]
except KeyError:
    st.error("DART API 키가 설정되어 있지 않습니다. Streamlit Cloud에서 시크릿을 설정해주세요.")
    st.info("Streamlit Cloud에서 'Settings' > 'Secrets' 메뉴로 이동하여 'DART_API_KEY'를 추가해주세요.")
    st.stop()

dart = OpenDartReader(api_key)

# ✅ Streamlit 기본 설정
st.set_page_config(page_title="재무제표 조회 앱", layout="centered")
st.title("📊 재무제표 조회 및 다운로드 앱")

st.markdown("회사명을 입력하면 최근 연도의 재무제표를 불러와 보여드릴게요.")

# ✅ 사용자 입력
company_name = st.text_input("회사명을 입력하세요 (예: 삼성전자)", "삼성전자")

# 연도 선택 옵션 추가
current_year = datetime.today().year
years = list(range(current_year-5, current_year))
selected_year = st.selectbox("조회할 연도를 선택하세요", years, index=0)

# ✅ 조회 버튼
if st.button("📥 재무제표 조회 및 다운로드"):
    if not company_name:
        st.warning("회사명을 입력해주세요.")
    else:
        with st.spinner(f"'{company_name}'의 정보를 조회 중입니다..."):
            try:
                corp_code = dart.find_corp_code(company_name)

                if corp_code is None:
                    st.error(f"❌ '{company_name}'의 고유번호를 찾을 수 없습니다.")
                else:
                    try:
                        fs = dart.finstate(corp_code, selected_year)

                        if fs is None or fs.empty:
                            st.warning(f"'{company_name}'의 {selected_year}년도 재무제표를 찾을 수 없습니다.")
                        else:
                            output_df = fs[['sj_nm', 'account_nm', 'thstrm_amount', 'frmtrm_amount']]
                            
                            # 컬럼명을 한글로 변경
                            output_df = output_df.rename(columns={
                                'sj_nm': '재무제표명',
                                'account_nm': '계정과목',
                                'thstrm_amount': f'{selected_year}년',
                                'frmtrm_amount': f'{selected_year-1}년'
                            })
                            
                            st.success(f"✅ '{company_name}'의 {selected_year}년 재무제표를 불러왔습니다.")
                            st.dataframe(output_df)

                            # ✅ 엑셀 파일 버퍼로 저장
                            def to_excel(df):
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    df.to_excel(writer, index=False, sheet_name='재무제표')
                                output.seek(0)  # 버퍼의 포인터를 처음으로 되돌림
                                return output.getvalue()

                            excel_data = to_excel(output_df)

                            st.download_button(
                                label="📂 엑셀로 다운로드",
                                data=excel_data,
                                file_name=f"{company_name}_{selected_year}_재무제표.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.error(f"❌ 재무제표 조회 중 오류 발생: {e}")
            except Exception as e:
                st.error(f"❌ 회사 정보 조회 중 오류 발생: {e}")

# 설명 추가
with st.expander("📝 사용 방법"):
    st.markdown("""
    1. DART API 키가 필요합니다. [DART 오픈API](https://opendart.fss.or.kr/) 사이트에서 발급받을 수 있습니다.
    2. 회사명을 입력하고 조회할 연도를 선택합니다.
    3. '재무제표 조회 및 다운로드' 버튼을 클릭합니다.
    4. 조회된 재무제표는 엑셀 파일로 다운로드할 수 있습니다.
    
    **참고**: 이 앱은 OpenDartReader 패키지를 사용합니다.
    """)

# 푸터 추가
st.markdown("---")
st.markdown("© 2025 재무제표 조회 앱 | 데이터 출처: [금융감독원 DART](https://dart.fss.or.kr/)")
