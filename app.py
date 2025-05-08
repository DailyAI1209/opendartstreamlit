import streamlit as st
import pandas as pd
from OpenDartReader import OpenDartReader
from io import BytesIO
import json

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
fs_type = st.selectbox("재무제표 유형", ["재무상태표", "손익계산서"], index=0)

# 재무제표 유형 매핑 정의
sj_mapping = {
    'BS': '재무상태표',
    'IS': '손익계산서',
    'CIS': '포괄손익계산서',
    'CF': '현금흐름표',
    'SCE': '자본변동표'
}

# 역방향 매핑 추가
reverse_sj_mapping = {v: k for k, v in sj_mapping.items()}

# 상세 계정과목 수동 추가 (재무상태표)
bs_accounts = [
    {"account_nm": "유동자산", "account_detail": "회사의 1년 이내 현금화 가능한 자산"},
    {"account_nm": "비유동자산", "account_detail": "회사의 1년 이후 현금화 가능한 자산"},
    {"account_nm": "자산총계", "account_detail": "유동자산과 비유동자산의 합계"},
    {"account_nm": "유동부채", "account_detail": "회사의 1년 이내 상환해야 할 부채"},
    {"account_nm": "비유동부채", "account_detail": "회사의 1년 이후 상환해야 할 부채"},
    {"account_nm": "부채총계", "account_detail": "유동부채와 비유동부채의 합계"},
    {"account_nm": "자본금", "account_detail": "주주가 납입한 금액"},
    {"account_nm": "이익잉여금", "account_detail": "회사의 누적 이익"},
    {"account_nm": "자본총계", "account_detail": "자본금, 이익잉여금 등의 합계"}
]

# 상세 계정과목 수동 추가 (손익계산서)
is_accounts = [
    {"account_nm": "매출액", "account_detail": "회사의 주요 영업 활동에 의한 수익"},
    {"account_nm": "매출원가", "account_detail": "매출을 달성하기 위해 투입된 비용"},
    {"account_nm": "매출총이익", "account_detail": "매출액에서 매출원가를 뺀 이익"},
    {"account_nm": "판매비와관리비", "account_detail": "판매 및 관리 활동에 소요된 비용"},
    {"account_nm": "영업이익", "account_detail": "매출총이익에서 판매비와관리비를 뺀 이익"},
    {"account_nm": "영업외수익", "account_detail": "주요 영업 활동 이외의 수익"},
    {"account_nm": "영업외비용", "account_detail": "주요 영업 활동 이외의 비용"},
    {"account_nm": "법인세차감전순이익", "account_detail": "법인세 공제 전 이익"},
    {"account_nm": "법인세비용", "account_detail": "법인세로 납부해야 할 비용"},
    {"account_nm": "당기순이익", "account_detail": "최종적인 회계기간 동안의 이익"}
]

# 4. 버튼 클릭 시 데이터 조회
if st.button("📥 재무제표 조회"):
    with st.spinner("📡 DART로부터 데이터를 가져오는 중입니다..."):
        try:
            # 기본 재무제표 조회
            df = dart.finstate(company_name.strip(), int(year))
            
            if df is not None and not df.empty:
                st.success(f"✅ {company_name}의 {year}년 재무제표를 불러왔습니다.")
                
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
                
                # sj_nm/sj_div 컬럼의 약자를 전체 이름으로 변환
                if sj_column:
                    # 컬럼명을 'sj_nm'으로 통일
                    if sj_column == 'sj_div':
                        df_show.rename(columns={'sj_div': 'sj_nm'}, inplace=True)
                    
                    # 약자를 전체 이름으로 변환
                    df_show['sj_nm'] = df_show['sj_nm'].apply(
                        lambda x: sj_mapping.get(x, x) if x in sj_mapping else x
                    )
                
                # 선택한 재무제표 유형에 해당하는 상세 데이터 생성
                sj_code = reverse_sj_mapping.get(fs_type, 'BS')
                selected_accounts = bs_accounts if sj_code == 'BS' else is_accounts
                
                # 기존 데이터에서 선택한 재무제표 유형의 항목들만 필터링
                filtered_df = df_show[df_show['sj_nm'] == fs_type].copy() if sj_column else df_show.copy()
                
                # 필터링된 데이터에서 자산총계, 매출액 등의 주요 값 추출
                key_values = {}
                for row in filtered_df.itertuples():
                    account = getattr(row, 'account_nm')
                    if 'thstrm_amount' in filtered_df.columns:
                        amount = getattr(row, 'thstrm_amount')
                        key_values[account] = amount
                
                # 상세 계정과목 데이터프레임 생성
                detailed_data = []
                for account in selected_accounts:
                    row_data = {
                        'sj_nm': fs_type,
                        'account_nm': account['account_nm'],
                        'thstrm_amount': key_values.get(account['account_nm'], 0)
                    }
                    if 'frmtrm_amount' in filtered_df.columns:
                        # 전기 데이터가 있으면 추가
                        row_data['frmtrm_amount'] = 0  # 기본값
                    detailed_data.append(row_data)
                
                # 상세 데이터프레임 생성
                detailed_df = pd.DataFrame(detailed_data)
                
                # 표시할 상세 재무제표
                st.dataframe(detailed_df, use_container_width=True)
                
                # Excel 다운로드 기능 추가
                def to_excel(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='재무제표')
                    output.seek(0)  # 버퍼의 포인터를 처음으로 되돌림
                    return output.getvalue()
                
                excel_data = to_excel(detailed_df)
                
                st.download_button(
                    label="📂 엑셀로 다운로드",
                    data=excel_data,
                    file_name=f"{company_name}_{year}_{fs_type}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # CSV 다운로드 옵션도 유지
                csv = detailed_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📤 CSV로 다운로드",
                    data=csv,
                    file_name=f"{company_name}_{year}_{fs_type}.csv",
                    mime='text/csv'
                )
            else:
                st.warning(f"⚠️ {company_name}의 {year}년 재무제표가 존재하지 않거나 공시되지 않았어요.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
