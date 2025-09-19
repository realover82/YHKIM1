import streamlit as st
import pandas as pd
import io
import plotly.express as px
from datetime import datetime, timedelta

# 'openpyxl' 및 'plotly' 라이브러리가 설치되어 있어야 XLSX 파일을 처리하고 차트를 생성할 수 있습니다.
# 설치 명령어: pip install openpyxl plotly-express

# --- XLSX 파일 분석 및 표시 함수 ---
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
        st.write(df.describe())
        
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

# --- 메인 애플리케이션 로직 ---
def main():
    st.set_page_config(layout="wide")
    st.title("통합 데이터 분석 및 조회 시스템")
    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["엑셀 파일 업로드", "파일 내용 조회 및 검색", "가격 변동 차트"])

    # 탭 1: 엑셀 파일 업로드
    with tab1:
        st.header("엑셀 파일 업로드")
        st.write("분석을 원하는 XLSX 파일을 업로드하세요.")
        uploaded_file = st.file_uploader("파일 선택", type=["xlsx"])
        if uploaded_file:
            display_excel_analysis_result(uploaded_file)
        else:
            if 'df_data' in st.session_state:
                del st.session_state['df_data']

    # 탭 2: 파일 내용 조회 및 검색
    with tab2:
        st.header("업로드된 파일 조회 및 검색")
        
        if 'df_data' in st.session_state and not st.session_state.df_data.empty:
            df_to_use = st.session_state.df_data

            # DB 조회 버튼
            if st.button("파일 내용 전체 조회"):
                st.write("업로드된 파일의 전체 내용입니다.")
                st.dataframe(df_to_use)

            st.markdown("---")
            st.header("파일 내용 검색")
            search_query = st.text_input("상품명, 상품 코드 등으로 검색하세요.", placeholder="예: 노트북")
            
            # 검색 버튼
            if st.button("검색"):
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
        else:
            st.info("데이터를 조회하려면 먼저 '엑셀 파일 업로드' 탭에서 파일을 업로드해주세요.")

    # 탭 3: 가격 변동 차트
    with tab3:
        st.header("가격 변동 차트")
        st.write("업로드된 파일의 '가격'과 '날짜' 열을 기준으로 가격 변동 차트를 생성합니다.")
        
        if 'df_data' in st.session_state and not st.session_state.df_data.empty:
            df_to_chart = st.session_state.df_data
            
            # 차트 생성을 위해 필요한 열('날짜', '가격')이 있는지 확인
            if '날짜' in df_to_chart.columns and '가격' in df_to_chart.columns:
                days_to_show = st.slider("지난 몇 일간의 데이터를 표시할까요?", 1, 30, 7)
                
                if st.button("차트 보기"):
                    # '날짜' 열을 datetime 타입으로 변환
                    df_to_chart['날짜'] = pd.to_datetime(df_to_chart['날짜'])
                    
                    # 슬라이더 값에 따라 데이터 필터링
                    filtered_chart_df = df_to_chart[df_to_chart['날짜'] >= datetime.now() - timedelta(days=days_to_show)]
                    
                    if not filtered_chart_df.empty:
                        st.subheader(f"지난 {days_to_show}일간의 가격 변동")
                        
                        # Plotly를 사용하여 차트 생성
                        fig = px.line(filtered_chart_df, x='날짜', y='가격', title='상품 가격 변동 추이')
                        fig.update_layout(xaxis_title="날짜", yaxis_title="가격(원)", hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("선택한 기간에 해당하는 차트 데이터가 없습니다.")
            else:
                st.warning("차트를 생성하려면 업로드된 파일에 '날짜'와 '가격' 열이 포함되어 있어야 합니다.")
        else:
            st.info("차트를 보려면 먼저 '엑셀 파일 업로드' 탭에서 파일을 업로드해주세요.")

if __name__ == "__main__":
    main()
