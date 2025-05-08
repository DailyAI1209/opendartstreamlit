import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import traceback

# 페이지 설정
st.set_page_config(page_title="재무제표 조회 앱", layout="centered")
st.title("📊 재무제표 조회 및 다운로드 앱")

# 에러 처리를 위한 함수
def handle_error(error_msg):
    st.error(f"❌ 오류 발생: {error_msg}")
    st.stop()

# OpenDartReader 가져오기 시도 - 수정된 부분
try:
    # 올바른 import 방식으로 수정
    from OpenDartReader import OpenDartReader
except ImportError:
    handle_error("OpenDartReader 패키지를 설치해주세요. (pip install opendartreader)")

# API 키 설정
try:
    # Streamlit Cloud에서는 st.secrets에서 가져옴
    api_key = st.secrets["DART_API_KEY"]
    st.success("✅ API 키를 성공적으로 불러왔습니다.")
except Exception:
    # 로컬에서 실행 시 또는 secrets가 없을 경우
    st.info("Streamlit Cloud의 Secrets에서 DART_API_KEY를 찾을 수 없습니다. 직접 입력해주세요.")
    api_key = st.text_input("DART API 키를 입력하세요", type="password")
    if not api_key:
        st.warning("⚠️ DART API 키가 필요합니다. API 키 없이는 앱을 사용할 수 없습니다.")
        st.markdown("""
        ### API 키 발급 방법
        1. [DART 오픈API](https://opendart.fss.or.kr/) 사이트에 접속
        2. 회원가입 및 로그인
        3. 인증키 신청/관리 메뉴에서 API 키 발급
        """)
        st.stop()

# 안내 메시지
st.markdown("회사명을 입력하면 해당 회사의 재무제표를 불러와 보여드립니다.")

# 사용자 입력
company_name = st.text_input("회사명을 입력하세요 (예: 삼성전자)", "삼성전자")

# 연도 선택 옵션
current_year = datetime.today().year
year = st.selectbox("조회할 연도를 선택하세요", range(current_year-5, current_year), index=1)

# OpenDartReader 초기화 (try-except로 감싸서 오류 처리)
try:
    with st.spinner("DART API 연결 중..."):
        # 올바른 클래스 호출 방식
        dart = OpenDartReader(api_key)
except Exception as e:
    error_details = traceback.format_exc()
    handle_error(f"OpenDartReader 초기화 실패: {str(e)}\n\n상세 오류: {error_details}")

# 조회 버튼
if st.button("📥 재무제표 조회 및 다운로드"):
    if not company_name:
        st.warning("⚠️ 회사명을 입력해주세요.")
    else:
        with st.spinner(f"'{company_name}'의 재무제표를 조회 중입니다..."):
            try:
                # 회사 코드 찾기
                corp_code = dart.find_corp_code(company_name)
                
                if corp_code is None:
                    st.error(f"❌ '{company_name}'의 고유번호를 찾을 수 없습니다. 회사명을 정확히 입력해주세요.")
                else:
                    # 재무제표 가져오기
                    try:
                        fs = dart.finstate(corp_code, year)
                        
                        if fs is None or fs.empty:
                            st.warning(f"⚠️ '{company_name}'의 {year}년도 재무제표를 찾을 수 없습니다.")
                        else:
                            # 필요한 컬럼만 선택
                            output_df = fs[['sj_nm', 'account_nm', 'thstrm_amount', 'frmtrm_amount']]
                            
                            # 컬럼명 한글화
                            output_df = output_df.rename(columns={
                                'sj_nm': '재무제표 종류',
                                'account_nm': '계정과목',
                                'thstrm_amount': f'{year}년',
                                'frmtrm_amount': f'{year-1}년'
                            })
                            
                            st.success(f"✅ '{company_name}'의 {year}년 재무제표를 불러왔습니다.")
                            
                            # 재무제표 종류별로 탭 나누기
                            unique_statements = output_df['재무제표 종류'].unique()
                            
                            if len(unique_statements) > 0:
                                tabs = st.tabs(unique_statements)
                                
                                for i, statement_type in enumerate(unique_statements):
                                    with tabs[i]:
                                        filtered_df = output_df[output_df['재무제표 종류'] == statement_type]
                                        st.dataframe(filtered_df, use_container_width=True)
                                
                                # 엑셀 파일 버퍼로 저장
                                def to_excel(df):
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                        # 각 재무제표 유형별로 시트 생성
                                        for statement_type in unique_statements:
                                            sheet_df = df[df['재무제표 종류'] == statement_type]
                                            # 시트명 31자 제한
                                            sheet_name = statement_type[:31]
                                            sheet_df.to_excel(writer, index=False, sheet_name=sheet_name)
                                    output.seek(0)  # 버퍼의 포인터를 처음으로 되돌림
                                    return output.getvalue()

                                excel_data = to_excel(output_df)

                                st.download_button(
                                    label="📂 엑셀로 다운로드",
                                    data=excel_data,
                                    file_name=f"{company_name}_{year}_재무제표.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            else:
                                st.warning("⚠️ 재무제표 데이터가 비어있습니다.")
                    except Exception as e:
                        st.error(f"❌ 재무제표 조회 중 오류 발생: {e}")
            except Exception as e:
                st.error(f"❌ 회사 정보 조회 중 오류 발생: {e}")

# 푸터 추가
st.markdown("---")
st.markdown("### 사용 방법")
st.markdown("""
1. 회사명을 입력하세요 (예: 삼성전자, SK하이닉스 등)
2. 조회할 연도를 선택하세요
3. '재무제표 조회 및 다운로드' 버튼을 클릭하세요
4. 재무제표 데이터를 확인하고 필요시 엑셀로 다운로드하세요
""")

# 도움말
with st.expander("❓ 자주 묻는 질문"):
    st.markdown("""
    **Q: API 키는 어디서 발급받나요?**  
    A: [DART 오픈API](https://opendart.fss.or.kr/) 사이트에서 회원가입 후 발급받을 수 있습니다.
    
    **Q: 특정 회사가 검색되지 않아요.**  
    A: 정확한 회사명을 입력했는지 확인해주세요. 상장사 기준으로 검색됩니다.
    
    **Q: 특정 연도의 데이터가 없어요.**  
    A: 해당 연도에 공시된 데이터가 없는 경우일 수 있습니다. 다른 연도를 선택해보세요.
    """)

st.markdown("---")
st.markdown("OpenDartReader와 Streamlit으로 제작된 재무제표 조회 앱입니다.")
