import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

font_path = './NanumGothic.ttf'
font = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font)
plt.rcParams['axes.unicode_minus'] = False



st.set_page_config(page_title="제로웨이스트 소비 분석", layout="wide")


# --------------------------------------------------------------------
# 분석 함수
# --------------------------------------------------------------------
def load_and_analyze_data(file, sheet_name='Sheet1'):

    # --- 1. 상수 정의 ---
    GREEN_KEYWORDS = [
        '리필', 'refill', '재활용', '업사이클', '대나무', '천연수세미',
        '제로웨이스트', '친환경', '에코백', '고체비누', '소프넛',
        '스테인리스 빨대', '다회용', '용기내'
    ]

    CO2_SAVINGS_MAP = {
        '리필': 0.2, 'refill': 0.2, '용기내': 0.2,
        '재활용': 0.1, '업사이클': 0.15,
        '고체비누': 0.15, '소프넛': 0.1,
        '천연수세미': 0.05, '대나무': 0.05,
        '에코백': 0.5, '스테인리스 빨대': 0.05
    }

    BASE_EMISSION_MAP = {
        '리필': 0.7, 'refill': 0.7, '용기내': 0.7,
        '재활용': 0.4, '업사이클': 0.4,
        '고체비누': 0.7, '소프넛': 0.7,
        '천연수세미': 0.15, '대나무': 0.1,
        '에코백': 0.5, '스테인리스 빨대': 0.05
    }
    DEFAULT_BASE_EMISSION = 0.4

    ITEM_COLUMN = '구매 품목'
    COST_COLUMN = '금액'
    QUANTITY_COLUMN = '수량'
    CO2_EMISSION_COLUMN = '탄소 배출량(kg)'
    TOTAL_COST_COLUMN = '총금액' # 수량x금액을 저장할 새로운 컬럼

    # --- 2. 데이터 읽기 및 전처리 ---
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"❌ 엑셀 파일을 불러오는 중 오류 발생: {e}")
        return None

    if ITEM_COLUMN not in df.columns or COST_COLUMN not in df.columns:
        st.error(f"❌ 엑셀에 '{ITEM_COLUMN}' 또는 '{COST_COLUMN}' 컬럼이 없습니다.")
        return None

    # 금액 컬럼 정제 및 float 변환 (개당 금액)
    df[COST_COLUMN] = (
        df[COST_COLUMN].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', 0)
        .astype(float)
    )
    df[ITEM_COLUMN] = df[ITEM_COLUMN].fillna('').astype(str).str.lower()

    # 수량 컬럼 정제 및 int 변환 (없으면 기본값 1)
    if QUANTITY_COLUMN not in df.columns:
        df[QUANTITY_COLUMN] = 1
    else:
        df[QUANTITY_COLUMN] = (
            df[QUANTITY_COLUMN]
            .astype(str)
            .str.replace(r'[^\d]', '', regex=True)
            .replace('', 0)
            .astype(int)
        )

    # --- 총금액 (수량 * 금액) 계산 ---
    df[TOTAL_COST_COLUMN] = df[COST_COLUMN] * df[QUANTITY_COLUMN]


    # 친환경 여부 플래그 설정
    df['친환경 여부'] = False
    for keyword in GREEN_KEYWORDS:
        df.loc[df[ITEM_COLUMN].str.contains(keyword), '친환경 여부'] = True

    # --- 3. CO2 계산 (수량 반영) ---
    df['CO2_절감량(kg)'] = 0.0
    for keyword, savings in CO2_SAVINGS_MAP.items():
        # 절감량 = 수량 * 개당 절감량
        df.loc[df[ITEM_COLUMN].str.contains(keyword) & df['친환경 여부'], 'CO2_절감량(kg)'] = \
            df[QUANTITY_COLUMN] * savings

    total_co2_savings = df['CO2_절감량(kg)'].sum()

    if CO2_EMISSION_COLUMN in df.columns:
        df[CO2_EMISSION_COLUMN] = (
            df[CO2_EMISSION_COLUMN].astype(str)
            .str.replace(r'[^\d.]', '', regex=True)
            .replace('', 0)
            .astype(float)
        )
        total_actual_co2 = df[CO2_EMISSION_COLUMN].sum()
        total_conventional_co2 = total_actual_co2 + total_co2_savings
        co2_calculation_method = "실제 기록된 값 기반"

    else:
        # 기준 배출량 = 수량 * 개당 기준 배출량
        df['CO2_기준배출량(kg)'] = df[QUANTITY_COLUMN] * DEFAULT_BASE_EMISSION
        for keyword, emission in BASE_EMISSION_MAP.items():
            df.loc[df[ITEM_COLUMN].str.contains(keyword), 'CO2_기준배출량(kg)'] = \
                df[QUANTITY_COLUMN] * emission

        total_conventional_co2 = df['CO2_기준배출량(kg)'].sum()
        total_actual_co2 = total_conventional_co2 - total_co2_savings
        co2_calculation_method = "추정치 기반"

    # --- 4. 금액 분석 (총금액 기준) ---
    total_cost = df[TOTAL_COST_COLUMN].sum()
    eco_cost = df.loc[df['친환경 여부'], TOTAL_COST_COLUMN].sum()
    eco_ratio = (eco_cost / total_cost) * 100 if total_cost > 0 else 0.0

    # --- 5. Streamlit 출력 ---
    st.subheader("📊 소비 금액 지표")
    st.write(f"**총 소비 금액:** {total_cost:,.0f} 원")
    st.write(f"**친환경 소비 금액:** {eco_cost:,.0f} 원")
    st.write(f"**친환경 소비 비율:** {eco_ratio:.1f}%")

    st.subheader(f"🌲 환경 기여 지표 ({co2_calculation_method})")
    st.write(f"**총 CO₂ (기준) 배출량:** {total_conventional_co2:.2f} kg")
    st.write(f"**총 CO₂ (실제) 배출량:** {total_actual_co2:.2f} kg")
    st.write(f"**총 CO₂ 절감량:** {total_co2_savings:.2f} kg")
    st.write(f"➡ 승용차 주행 약 **{total_co2_savings / 0.17:.0f} km** 절약 효과")

    eco_items = df[df['친환경 여부']][ITEM_COLUMN].unique()
    st.subheader("✅ 친환경으로 분류된 품목 (최대 10개)")
    if len(eco_items) > 0:
        st.write(eco_items[:10])
    else:
        st.write("없음")

    st.subheader("📈 친환경 여부별 소비 금액 비교")
    # 총금액 컬럼을 사용하여 차트 데이터 계산
    eco_vs_non_cost = df.groupby('친환경 여부')[TOTAL_COST_COLUMN].sum()
    eco_vs_non_cost.index = eco_vs_non_cost.index.map({True: '친환경 소비', False: '일반 소비'})
    st.bar_chart(eco_vs_non_cost)

    st.subheader("🔥 CO₂ 절감량 상위 10개 품목")
    top10_co2 = (
        df.groupby(ITEM_COLUMN)['CO2_절감량(kg)']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(top10_co2)

    st.subheader("🥧 카테고리별 소비 금액 비율")
    # 총금액 컬럼을 사용하여 차트 데이터 계산
    category_cost = df.groupby(ITEM_COLUMN)[TOTAL_COST_COLUMN].sum()
    
    fig, ax = plt.subplots(figsize=(8, 8))
    # 데이터가 너무 많을 경우 상위 10개만 표시
    if len(category_cost) > 10:
        # 기타 항목으로 묶기
        top_n = 9
        top_categories = category_cost.nlargest(top_n)
        other_sum = category_cost.iloc[top_n:].sum()
        
        # '기타' 항목이 0인 경우를 대비
        if other_sum > 0:
            category_cost_for_chart = pd.concat([top_categories, pd.Series([other_sum], index=['기타'])])
        else:
            category_cost_for_chart = top_categories
    else:
        category_cost_for_chart = category_cost

    ax.pie(
        category_cost_for_chart, 
        labels=category_cost_for_chart.index, 
        autopct="%1.1f%%", 
        startangle=90,
        textprops={'fontsize': 10}
    )
    ax.axis("equal") # 원형 파이 차트 유지
    
    st.pyplot(fig)
    
    st.subheader("📋 전체 데이터 (수량 및 총금액 반영)")
    st.dataframe(df)

    return df


# --------------------------------------------------------------------
# Streamlit 화면 UI
# --------------------------------------------------------------------
st.title("🌿 제로 웨이스트 소비 분석 대시보드")

uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요 (.xlsx)", type=["xlsx"])
sheet_name = st.text_input("시트 이름 입력", value="Sheet1")

if st.button("분석 시작하기 🚀"):
    if uploaded_file is None:
        st.warning("⚠ 엑셀 파일을 먼저 업로드하세요.")
    else:
        st.success("분석을 시작합니다!")
        # 로딩 스피너 추가
        with st.spinner('데이터를 분석 중입니다...'):
            load_and_analyze_data(uploaded_file, sheet_name)





