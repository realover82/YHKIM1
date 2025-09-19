import streamlit as st
import pandas as pd
import io
import plotly.express as px
from datetime import datetime, timedelta

# 'openpyxl' 및 'plotly' 라이브러리가 설치되어 있어야 XLSX 파일을 처리하고 차트를 생성할 수 있습니다.
# 설치 명령어: pip install openpyxl plotly-express

# --- 데이터베이스 역할을 할 샘플 데이터 생성 ---
# 실제 DB에 연결하려면 이 부분을 수정해야 합니다.
@st.cache_data
# def load_db_data():
#     """
#     샘플 데이터를 로드하여 데이터베이스처럼 사용합니다.
#     실제 사용 시에는 이 함수를 데이터베이스에서 데이터를 가져오는 코드로 대체해야 합니다.
#     """
#     data = {
#         '상품_코드': ['P101', 'P102', 'P103', 'P104', 'P105'],
#         '상품명': ['스마트폰', '노트북', '무선 이어폰', '스마트워치', '태블릿'],
#         '가격': [1200000, 1500000, 250000, 400000, 800000],
#         '재고수량': [150, 80, 500, 200, 120],
#         '최근_업데이트': [
#             datetime.now() - timedelta(days=2),
#             datetime.now() - timedelta(days=5),
#             datetime.now() - timedelta(days=1),
#             datetime.now() - timedelta(days=3),
#             datetime.now() - timedelta(days=10)
#         ]
#     }
#     return pd.DataFrame(data)

# --- XLSX 파일 분석 및 표시 함수 ---
def display_excel_analysis_result(uploaded_file):
    """업로드된 XLSX 파일 내용을 읽고 Streamlit에 표시하는 함수"""
    try:
        # XLSX 파일 읽기
        df = pd.read_excel(uploaded_file)
        st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")
        st.markdown("---")
        st.subheader("업로드된 파일 내용 미리보기")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("분석 요약")
        st.write(df.describe())
        
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

# --- 메인 애플리케이션 로직 ---
def main():
    st.set_page_config(layout="wide")
    st.title("데이터 분석 및 조회 시스템")
    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["엑셀 파일 업로드 및 분석", "DB 조회 및 검색", "가격 변동 차트"])

    # 탭 1: 엑셀 파일 업로드 및 분석
    with tab1:
        st.header("엑셀 파일 업로드")
        st.write("분석을 원하는 XLSX 파일을 업로드하세요.")
        uploaded_file = st.file_uploader("파일 선택", type=["xlsx"])
        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
            display_excel_analysis_result(uploaded_file)
        else:
            if 'uploaded_file' in st.session_state:
                del st.session_state['uploaded_file']

    # 탭 2: DB 조회 및 검색
    with tab2:
        st.header("DB 조회")
        
        # 세션 상태에 데이터프레임이 없으면 로드
        if 'db_df' not in st.session_state:
            st.session_state.db_df = load_db_data()
            st.session_state.filtered_df = st.session_state.db_df.copy()

        # DB 조회 버튼
        if st.button("DB 내용 조회"):
            st.write("데이터베이스의 전체 내용입니다.")
            st.dataframe(st.session_state.db_df)

        st.markdown("---")
        st.header("DB 검색")
        search_query = st.text_input("상품명, 상품 코드 등으로 검색하세요.", placeholder="예: 노트북")
        
        # 검색 버튼
        if st.button("검색"):
            if search_query:
                # 대소문자 구분 없이 검색
                filtered_df = st.session_state.db_df[
                    st.session_state.db_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                ]
                if not filtered_df.empty:
                    st.session_state.filtered_df = filtered_df
                    st.success(f"'{search_query}'(으)로 검색된 결과입니다.")
                    st.dataframe(st.session_state.filtered_df)
                else:
                    st.warning(f"'{search_query}'에 대한 검색 결과가 없습니다.")
                    st.session_state.filtered_df = pd.DataFrame() # 결과 초기화
            else:
                st.info("검색어를 입력해주세요.")
                st.session_state.filtered_df = st.session_state.db_df.copy()

    # 탭 3: 가격 변동 차트
    with tab3:
        st.header("가격 변동 차트")
        st.write("마지막 가격 변동일로부터 지난 며칠간의 가격 변동을 보여주는 차트입니다.")
        
        # 차트 생성을 위한 샘플 데이터 (시간에 따른 가격 변화)
        chart_data = {
            '날짜': [datetime.now() - timedelta(days=i) for i in range(10, 0, -1)],
            '가격': [
                1100000, 1150000, 1200000, 1250000, 1220000, 
                1240000, 1250000, 1260000, 1270000, 1280000
            ]
        }
        df_chart = pd.DataFrame(chart_data)

        days_to_show = st.slider("지난 몇 일간의 데이터를 표시할까요?", 1, 10, 7)
        
        # 차트 버튼
        if st.button("차트 보기"):
            # 슬라이더 값에 따라 데이터 필터링
            filtered_chart_df = df_chart[df_chart['날짜'] >= datetime.now() - timedelta(days=days_to_show)]
            
            if not filtered_chart_df.empty:
                st.subheader(f"지난 {days_to_show}일간의 가격 변동")
                
                # Plotly를 사용하여 차트 생성
                fig = px.line(filtered_chart_df, x='날짜', y='가격', title='상품 가격 변동 추이')
                fig.update_layout(xaxis_title="날짜", yaxis_title="가격(원)", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("선택한 기간에 해당하는 차트 데이터가 없습니다.")

if __name__ == "__main__":
    main()
