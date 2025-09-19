import streamlit as st
import pandas as pd
import io
import plotly.express as px
from datetime import datetime, timedelta
import logging

# Install 'openpyxl', 'plotly', and 'matplotlib' to handle XLSX files and generate charts.
# Installation command: pip install openpyxl plotly matplotlib

# Logging configuration (outputs logs to the Streamlit console)
logging.basicConfig(level=logging.INFO)

# --- XLSX File Analysis and Display Function (Called from Main Screen) ---
def display_excel_analysis_result(uploaded_file):
    """Reads the contents of an uploaded XLSX file and displays them in Streamlit"""
    try:
        # Read the XLSX file
        df = pd.read_excel(uploaded_file)
        st.session_state['df_data'] = df  # Store the uploaded file in session state
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

# --- Main Application Logic ---
def main():
    st.set_page_config(layout="wide")
    st.title("통합 데이터 분석 및 조회 시스템")
    st.markdown("---")

    # Initialize session state
    if 'show_search_results' not in st.session_state:
        st.session_state.show_search_results = False
    if 'show_chart' not in st.session_state:
        st.session_state.show_chart = False
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    # Sidebar: File Upload
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
    
    # Main screen
    if 'uploaded_file' in st.session_state:
        # Display analysis results only when a file is uploaded
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
                    # Search across all columns, case-insensitive
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
        st.header("Price Change Chart")
        st.write("Generates a chart showing the days elapsed since the last price change, based on the '자재명' (Material Name) and '효력시작일' (Effective Date) columns of the uploaded file.")
        
        if st.button("View Chart"):
            st.session_state.show_chart = True
        
        if st.session_state.show_chart:
            if 'df_data' in st.session_state and not st.session_state.df_data.empty:
                df_to_chart = st.session_state.df_data
                
                # Check for the required columns ('자재명', '효력시작일') for chart generation
                if '자재명' in df_to_chart.columns and '효력시작일' in df_to_chart.columns:
                    try:
                        # Convert '효력시작일' to datetime format
                        df_to_chart['효력시작일'] = pd.to_datetime(df_to_chart['효력시작일'])

                        # Calculate days elapsed from today
                        today = datetime.now()
                        df_to_chart['경과일수'] = (today - df_to_chart['효력시작일']).dt.days

                        # **--- Log added: Check data before filtering ---**
                        logging.info("--- [Log] Starting chart data filtering ---")
                        logging.info("Data before filtering:")
                        logging.info(df_to_chart[['자재명', '효력시작일', '경과일수']].to_string())

                        # Filter for entries where days elapsed is greater than 30
                        df_over_30_days = df_to_chart[df_to_chart['경과일수'] > 30].copy()

                        # **--- Log added: Check data after filtering ---**
                        logging.info("Data after filtering (> 30 days):")
                        logging.info(df_over_30_days[['자재명', '효력시작일', '경과일수']].to_string())
                        logging.info("--- [Log] Chart data filtering complete ---")

                        if not df_over_30_days.empty:
                            # Keep only the latest data for duplicate materials
                            df_sorted = df_over_30_days.sort_values(by=['자재명', '효력시작일'], ascending=[True, False])
                            df_unique_materials = df_sorted.drop_duplicates(subset='자재명')

                            # Sort by days elapsed in descending order
                            df_unique_materials = df_unique_materials.sort_values(by='경과일수', ascending=False)
                            
                            st.subheader('Materials with Price Changes Older Than 30 Days')
                            st.write("If the chart is not visible, please check if your file contains data matching the criteria or if the '자재명' and '효력시작일' columns exist.")

                            # Draw the chart using Plotly
                            fig = px.bar(
                                df_unique_materials,
                                x='경과일수',
                                y='자재명',
                                orientation='h',
                                title='Days Elapsed Since Last Price Change (> 30 Days)',
                                labels={'경과일수': 'Days Elapsed', '자재명': 'Material Name'},
                                text='경과일수',
                                color_discrete_sequence=['darkorange']
                            )
                            # Customize layout for better readability
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
                            st.info("No materials with price changes older than 30 days were found.")
                    except Exception as e:
                        st.error(f"An error occurred while generating the chart: {e}")
                else:
                    st.warning("To generate the chart, your uploaded file must contain the '자재명' and '효력시작일' columns.")

if __name__ == "__main__":
    main()
