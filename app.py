import streamlit as st
import pandas as pd
from OpenDartReader import OpenDartReader
from io import BytesIO
import time

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
            # 디버깅을 위한 로그 추가
            debug_log = st.empty()
            debug_log.info(f"검색 시작: {company_name}, {year}년도")
            
            # 다양한 방식으로 시도
            fs_options = ['OFS', 'CFS']  # OFS(재무제표), CFS(연결재무제표)
            reprt_options = ['11011', '11012', '11013', '11014']  # 1분기, 반기, 3분기, 사업
            
            df = None
            
            # 먼저 기본 방식으로 시도
            debug_log.info("기본 방식으로 시도 중...")
            df = dart.finstate(company_name.strip(), int(year))
            
            # 기본 방식이 실패하면 다양한 파라미터 조합 시도
            if df is None or df.empty or len(df) < 5:  # 충분한 데이터가 없으면
                debug_log.info("상세 데이터를 찾기 위해 다른 옵션 시도 중...")
                
                for fs_div in fs_options:
                    for reprt_code in reprt_options:
                        try:
                            debug_log.info(f"시도: fs_div={fs_div}, reprt_code={reprt_code}")
                            temp_df = dart.finstate(company_name.strip(), int(year), fs_div=fs_div, reprt_code=reprt_code)
                            
                            # 충분한 데이터가 있으면 선택
                            if temp_df is not None and not temp_df.empty and len(temp_df) > 5:
                                debug_log.success(f"성공! fs_div={fs_div}, reprt_code={reprt_code}에서 {len(temp_df)}개 항목 발견")
                                df = temp_df
                                break
                            
                            # API 요청 간 간격 두기
                            time.sleep(0.5)
                        except Exception as e:
                            debug_log.warning(f"옵션 시도 중 오류: {e}")
                    
                    if df is not None and not df.empty and len(df) > 5:
                        break
            
            # 디버그 로그 제거
            debug_log.empty()
            
            if df is not None and not df.empty:
                st.success(f"✅ {company_name}의 {year}년 재무제표입니다.")
                
                # 표시할 컬럼 선택
                available_columns = []
                
                # sj_nm 또는 sj_div 확인
                if 'sj_nm' in df.columns:
                    sj_column = 'sj_nm'
                elif 'sj_div' in df.columns:
                    sj_column = 'sj_div'
                else:
                    sj_column = None
                
                if sj_column:
                    available_columns.append(sj_column)
                
                # account_nm은 필수
                available_columns.append('account_nm')
                
                # 금액 컬럼 추가
                if 'thstrm_amount' in df.columns:
                    available_columns.append('thstrm_amount')
                
                if 'frmtrm_amount' in df.columns:
                    available_columns.append('frmtrm_amount')
                
                # 표시할 데이터 선택
                df_show = df[available_columns].copy()
                
                # 재무제표 유형 매핑 정의
                sj_mapping = {
                    'BS': '재무상태표',
                    'IS': '손익계산서',
                    'CIS': '포괄손익계산서',
                    'CF': '현금흐름표',
                    'SCE': '자본변동표'
                }
                
                # sj_nm/sj_div 컬럼의 약자를 전체 이름으로 변환
                if sj_column:
                    # 컬럼명을 'sj_nm'으로 통일
                    if sj_column == 'sj_div':
                        df_show.rename(columns={'sj_div': 'sj_nm'}, inplace=True)
                    
                    # 약자를 전체 이름으로 변환
                    df_show['sj_nm'] = df_show['sj_nm'].apply(
                        lambda x: sj_mapping.get(x, x) if x in sj_mapping else x
                    )
                
                st.dataframe(df_show, use_container_width=True)
                
                # Excel 다운로드 기능 추가
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
