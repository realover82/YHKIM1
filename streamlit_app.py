import streamlit as st
import pandas as pd
import io
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging

# 'openpyxl' 및 'plotly', 'matplotlib' 라이브러리가 설치되어 있어야 XLSX 파일을 처리하고 차트를 생성할 수 있습니다.
# 설치 명령어: pip install openpyxl plotly matplotlib

# 로그 설정 (Streamlit 콘솔에 로그 출력)
logging.basicConfig(level=logging.INFO)

# 한글 폰트 설정
# 시스템에 'Malgun Gothic' 폰트가 없으면 다른 폰트(예: 'NanumGothic')를 설치해야 합니다.
# Streamlit Cloud에서는 폰트 설치가 필요할 수 있습니다.
# matplotlib 폰트 캐시를 지우고 다시 빌드하는 과정이 필요할 수 있습니다.
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# --- XLSX 파일 분석 및 표시 함수 (메인 화면에서 호출) ---
def display_excel_analysis_result(uploaded_file):
    """업로드된 XLSX 파일 내용을 읽고 Streamlit에 표시하는 함수"""
    try:
        # XLSX 파일 읽기
        df = pd.read_excel(uploaded_file)
        st.session_state['df_data'] = df  # 업로드된 파일을 세션 상태에 저장
        st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")
        st.markdown("---")
        st.subheader("업로드된 파일 내용 미리보기")
        st.dataframe(df)

        st.markdown("---")
        st.subheader("분석 요약")
        st.write("아래 표는 데이터의 개수, 평균, 최소/최대값 등 주요 통계 정보를 요약해서 보여줍니다.")
        st.dataframe(df.describe())
        
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

# --- 메인 애플리케이션 로직 ---
def main():
    st.set_page_config(layout="wide")
    st.title("통합 데이터 분석 및 조회 시스템")
    st.markdown("---")

    # 세션 상태 초기화
    if 'show_search_results' not in st.session_state:
        st.session_state.show_search_results = False
    if 'show_chart' not in st.session_state:
        st.session_state.show_chart = False
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    # 사이드바: 파일 업로드
    with st.sidebar:
        st.header("엑셀 파일 업로드")
        st.write("분석을 원하는 XLSX 파일을 업로드하세요.")
        uploaded_file = st.file_uploader("파일 선택", type=["xlsx"])
        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
        else:
            if 'uploaded_file' in st.session_state:
                del st.session_state['uploaded_file']
            if 'df_data' in st.session_state:
                del st.session_state['df_data']
    
    # 메인 화면
    if 'uploaded_file' in st.session_state:
        # 파일이 업로드되었을 때만 분석 결과를 표시
        uploaded_file_obj = st.session_state['uploaded_file']
        display_excel_analysis_result(uploaded_file_obj)

        st.markdown("---")
        st.header("파일 내용 검색")
        search_query_input = st.text_input("상품명, 상품 코드 등으로 검색하세요.", key="search_input")
        
        if st.button("검색"):
            st.session_state.search_query = search_query_input
            st.session_state.show_search_results = True
        
        if st.session_state.show_search_results:
            if 'df_data' in st.session_state and not st.session_state.df_data.empty:
                df_to_use = st.session_state.df_data
                search_query = st.session_state.search_query

                if search_query:
                    # 모든 열에서 대소문자 구분 없이 검색
                    filtered_df = df_to_use[
                        df_to_use.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                    ]
                    if not filtered_df.empty:
                        st.success(f"'{search_query}'(으)로 검색된 결과입니다.")
                        st.dataframe(filtered_df)
                    else:
                        st.warning(f"'{search_query}'에 대한 검색 결과가 없습니다.")
                else:
                    st.info("검색어를 입력해주세요.")
        
        st.markdown("---")
        st.header("가격 변동 차트")
        st.write("업로드된 파일의 '자재명'과 '효력시작일' 열을 기준으로 가격 변동 경과일수를 보여주는 차트를 생성합니다.")
        
        if st.button("차트 보기"):
            st.session_state.show_chart = True
        
        if st.session_state.show_chart:
            if 'df_data' in st.session_state and not st.session_state.df_data.empty:
                df_to_chart = st.session_state.df_data
                
                # 차트 생성을 위해 필요한 열('자재명', '효력시작일')이 있는지 확인
                if '자재명' in df_to_chart.columns and '효력시작일' in df_to_chart.columns:
                    try:
                        # '효력시작일'을 날짜 형식으로 변환
                        df_to_chart['효력시작일'] = pd.to_datetime(df_to_chart['효력시작일'])

                        # 오늘 날짜를 기준으로 경과 일수 계산
                        today = datetime.now()
                        df_to_chart['경과일수'] = (today - df_to_chart['효력시작일']).dt.days

                        # **--- 로그 추가: 필터링 전 데이터 확인 ---**
                        logging.info("--- [로그] 차트 데이터 필터링 시작 ---")
                        logging.info("필터링 전 데이터:")
                        logging.info(df_to_chart[['자재명', '효력시작일', '경과일수']].to_string())

                        # 경과일수가 30일보다 큰 항목만 필터링
                        df_over_30_days = df_to_chart[df_to_chart['경과일수'] > 30].copy()

                        # **--- 로그 추가: 필터링 후 데이터 확인 ---**
                        logging.info("필터링 후 (30일 초과) 데이터:")
                        logging.info(df_over_30_days[['자재명', '효력시작일', '경과일수']].to_string())
                        logging.info("--- [로그] 차트 데이터 필터링 완료 ---")

                        if not df_over_30_days.empty:
                            # 중복된 자재는 가장 최신 데이터만 남기기
                            df_sorted = df_over_30_days.sort_values(by=['자재명', '효력시작일'], ascending=[True, False])
                            df_unique_materials = df_sorted.drop_duplicates(subset='자재명')

                            # 경과일수 기준 내림차순 정렬
                            df_unique_materials = df_unique_materials.sort_values(by='경과일수', ascending=False)
                            
                            st.subheader('가격 변경 후 30일 초과된 자재 목록')
                            st.write("차트가 보이지 않는다면, 파일에 해당 조건에 맞는 데이터가 없거나 '자재명' 또는 '효력시작일' 열이 없는지 확인해 보세요.")

                            # 차트 그리기
                            fig, ax = plt.subplots(figsize=(12, 8))
                            ax.barh(df_unique_materials['자재명'], df_unique_materials['경과일수'], color='darkorange')

                            # 차트 제목 및 축 레이블 설정
                            ax.set_title('가격 변경 후 경과 일수 (> 30일)', fontsize=16)
                            ax.set_xlabel('경과 일수', fontsize=12)
                            ax.set_ylabel('자재명', fontsize=12)
                            ax.invert_yaxis()

                            # 막대 위에 경과일수와 날짜 정보 추가
                            for bar, date in zip(ax.patches, df_unique_materials['효력시작일']):
                                width = bar.get_width()
                                ax.text(width, bar.get_y() + bar.get_height()/2, 
                                        f' {int(width)}일 (효력일: {date.strftime("%Y-%m-%d")})', 
                                        va='center', ha='left', fontsize=10, fontweight='bold')

                            plt.tight_layout()
                            st.pyplot(fig)
                        else:
                            st.info("가격 변경 후 30일 초과된 자재가 없습니다.")
                    except Exception as e:
                        st.error(f"차트를 생성하는 중 오류가 발생했습니다: {e}")
                else:
                    st.warning("차트를 생성하려면 업로드된 파일에 '자재명'과 '효력시작일' 열이 포함되어 있어야 합니다.")

if __name__ == "__main__":
    main()
