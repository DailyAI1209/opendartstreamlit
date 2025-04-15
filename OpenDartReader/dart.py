class OpenDartReader:
    def __init__(self, api_key):
        self.api_key = api_key

    def finstate(self, corp_name, year):
        import pandas as pd
        # 더미 데이터 반환 (실제 DART API 연결 필요)
        return pd.DataFrame({
            "sj_div": ["BS", "IS"],
            "account_nm": ["자산총계", "매출액"],
            "thstrm_amount": ["100,000", "200,000"]
        })
