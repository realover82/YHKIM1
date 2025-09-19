import streamlit as st
import pandas as pd
import io
import plotly.express as px
from datetime import datetime, timedelta
import logging

# 'openpyxl'과 'plotly' 라이브러리가 설치되어 있어야 XLSX 파일을 처리하고 차트를 생성할 수 있습니다.
# 설치 명령어: pip install openpyxl plotly

# 로그 설정 (Streamlit 콘솔에 로그 출력)
logging.basicConfig(level=logging.INFO)

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
        st.header("파일 내용 검색 및 차트 조회")
        search_query_input = st.text_input("자재명 또는 자재코드로 검색하세요.", key="search_input")
        
        if st.button("검색"):
            st.session_state.search_query = search_query_input
            st.session_state.show_search_results = True
            
        if st.session_state.show_search_results:
            if 'df_data' in st.session_state and not st.session_state.df_data.empty:
                df_to_use = st.session_state.df_data
                search_query = st.session_state.search_query

                if search_query:
                    # '자재명' 또는 '자재코드' 열에서 검색
                    if '자재명' in df_to_use.columns and '자재코드' in df_to_use.columns:
                        filtered_df = df_to_use[
                            df_to_use['자재명'].astype(str).str.contains(search_query, case=False) |
                            df_to_use['자재코드'].astype(str).str.contains(search_query, case=False)
                        ].copy()
                    elif '자재명' in df_to_use.columns:
                        filtered_df = df_to_use[
                            df_to_use['자재명'].astype(str).str.contains(search_query, case=False)
                        ].copy()
                    elif '자재코드' in df_to_use.columns:
                        filtered_df = df_to_use[
                            df_to_use['자재코드'].astype(str).str.contains(search_query, case=False)
                        ].copy()
                    else:
                        st.warning("검색을 위해 '자재명' 또는 '자재코드' 열이 필요합니다.")
                        filtered_df = pd.DataFrame() # 빈 데이터프레임으로 초기화

                    if not filtered_df.empty:
                        st.success(f"'{search_query}'(으)로 검색된 결과입니다.")
                        st.dataframe(filtered_df)

                        # 검색된 데이터로 차트 생성 및 표시
                        st.markdown("---")
                        st.header("가격 변동 차트")
                        st.write("검색된 자재의 가격 변동 경과일수를 보여주는 차트를 생성합니다.")
                        
                        if '효력시작일' in filtered_df.columns:
                            try:
                                filtered_df['효력시작일'] = pd.to_datetime(filtered_df['효력시작일'])
                                today = datetime.now()
                                filtered_df['경과일수'] = (today - filtered_df['효력시작일']).dt.days

                                if not filtered_df.empty:
                                    if '자재코드' in filtered_df.columns:
                                        filtered_df['차트_라벨'] = filtered_df['자재명'] + ' (' + filtered_df['자재코드'].astype(str) + ')'
                                        y_label = '차트_라벨'
                                    else:
                                        y_label = '자재명'

                                    fig = px.bar(
                                        filtered_df.sort_values(by='경과일수', ascending=False),
                                        x='경과일수',
                                        y=y_label,
                                        orientation='h',
                                        title=f'"{search_query}" 가격 변경 경과 일수',
                                        labels={'경과일수': '경과 일수'},
                                        text='경과일수',
                                        color_discrete_sequence=['darkorange']
                                    )
                                    fig.update_layout(
                                        yaxis={'autorange': 'reversed'},
                                        title_font_size=20,
                                        margin={'t': 50, 'b': 20},
                                        xaxis_title_font_size=14,
                                        yaxis_title_font_size=14
                                    )
                                    fig.update_traces(texttemplate='%{text} days', textposition='outside')
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("선택된 자재에 대한 데이터가 없습니다.")

                            except Exception as e:
                                st.error(f"차트를 생성하는 중 오류가 발생했습니다: {e}")
                        else:
                            st.warning("차트를 생성하려면 '효력시작일' 열이 포함되어 있어야 합니다.")
                    else:
                        st.warning(f"'{search_query}'에 대한 검색 결과가 없습니다.")
                else:
                    st.info("검색어를 입력해주세요.")
            
if __name__ == "__main__":
    main()
