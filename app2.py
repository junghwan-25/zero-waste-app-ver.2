import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 엑셀 파일 기본 컬럼명
ITEM_COLUMN = "구매 품목"
COST_COLUMN = "금액"
QUANTITY_COLUMN = "수량"
ECO_COLUMN = "친환경 여부"

# Streamlit 설정
st.set_page_config(page_title="친환경 소비 분석기", layout="wide")
st.title("🌱 친환경 소비 분석 페이지")

uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # 컬럼명 제대로 있는지 검사
    required_cols = {ITEM_COLUMN, COST_COLUMN, QUANTITY_COLUMN}
    if not required_cols.issubset(df.columns):
        st.error(f"엑셀 파일에 다음 항목이 있어야 합니다: {', '.join(required_cols)}")
        st.stop()

    # 불필요한 NanumGothic 설정 제거 (폰트 깨짐 방지)
    # plt.rc('font', family='NanumGothic')  # 삭제됨

    # 친환경 여부 컬럼 생성 (구매 품목명이 '친환경'을 포함하는지 기준)
    df[ECO_COLUMN] = df[ITEM_COLUMN].astype(str).str.contains("친환경")

    # 🟩 금액 × 수량 계산
    df["총금액"] = df[COST_COLUMN] * df[QUANTITY_COLUMN]

    # 총 소비 금액
    total_cost = df["총금액"].sum()

    # 친환경 제품 소비 금액
    eco_cost = df.loc[df[ECO_COLUMN], "총금액"].sum()

    # 비율 계산
    eco_ratio = (eco_cost / total_cost) * 100 if total_cost > 0 else 0.0

    st.subheader("📊 총 소비 분석 결과")
    st.write(f"**총 소비 금액:** {total_cost:,.0f}원")
    st.write(f"**친환경 제품 소비 금액:** {eco_cost:,.0f}원")
    st.write(f"**친환경 소비 비율:** {eco_ratio:.2f}%")

    st.divider()

    # 🥧 카테고리별 총 소비 금액 비율 그래프 (총금액 기준)
    st.subheader("🧁 카테고리별 소비 비율 (총금액 기준)")

    category_cost = df.groupby(ITEM_COLUMN)["총금액"].sum()

    fig, ax = plt.subplots()
    ax.pie(category_cost, labels=category_cost.index, autopct="%1.1f%%")
    ax.axis("equal")

    st.pyplot(fig)

    st.divider()

    st.subheader("📄 업로드된 데이터 미리보기")
    st.dataframe(df)

else:
    st.info("엑셀 파일을 업로드하면 자동으로 분석이 시작됩니다!")


