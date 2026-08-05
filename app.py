from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np

# Cấu hình trang
st.set_page_config(
    page_title="FTE Dashboard",
    page_icon="📊",
    layout="wide",
)

DATA_FILE = Path("FTE dashboard data.xlsx")

st.sidebar.title("📊VOLUME & FTE")

if not DATA_FILE.exists():
    st.error("Không tìm thấy file FTE dashboard data.xlsx. Hãy đặt file cùng thư mục với app.py.")
    st.stop()

# Đọc dữ liệu từ 4 sheet
@st.cache_data
def load_data():
    xls = pd.ExcelFile(DATA_FILE)
    df_hc = pd.read_excel(xls, "HC")
    df_monthly_vol = pd.read_excel(xls, "Monthly volume")
    df_office_fte = pd.read_excel(xls, "Office FTE")
    df_cs_fte = pd.read_excel(xls, "CS FTE")
    
    # Xóa các khoảng trắng thừa ở tên cột nếu có
    df_hc.columns = df_hc.columns.str.strip()
    df_office_fte.columns = df_office_fte.columns.str.strip()
    
    return df_hc, df_monthly_vol, df_office_fte, df_cs_fte

df_hc, df_monthly_vol, df_office_fte, df_cs_fte = load_data()

# Lấy danh sách các tháng (dựa trên cột Month của sheet HC)
months_list = df_hc['Month'].dropna().astype(str).unique().tolist()

# BỘ LỌC THÁNG (Sidebar)
st.sidebar.header("Bộ lọc")
selected_months = st.sidebar.multiselect(
    "Chọn Tháng",
    options=months_list,
    default=months_list
)

# Chuyển đổi dữ liệu CS FTE từ dạng cột sang dòng để dễ vẽ biểu đồ trend
df_cs_fte_melted = df_cs_fte.melt(id_vars=["CS PIC"], var_name="Month", value_name="FTE")
df_cs_fte_melted = df_cs_fte_melted[df_cs_fte_melted['FTE'].notna()]

# CHỌN TRANG
page = st.sidebar.radio("DASHBOARD MENU", ["Overview", "HC Status", "Monthly Volume"])

# HÀM LỌC DỮ LIỆU CHUNG
def filter_by_month(df, month_col="Month"):
    if not selected_months:
        return df.iloc[0:0] # Trả về df rỗng nếu không chọn tháng nào
    return df[df[month_col].astype(str).isin(selected_months)].copy()

if page == "Overview":
    st.title("Monthly Volume & FTE Overview")
    
    # Lọc dữ liệu
    hc_filtered = filter_by_month(df_hc)
    
    # Tính toán Metrics
    approved_hc = 11
    required_hc = hc_filtered['Required HC'].dropna().mean()
    workload_pct = hc_filtered['% Worload'].dropna().mean() if '% Worload' in hc_filtered.columns else hc_filtered['% Workload'].dropna().mean()
    
    # Lọc shipment volume (Trung bình tổng volume các cột tháng được chọn trong Monthly volume)
    valid_month_cols = [m for m in selected_months if m in df_monthly_vol.columns]
    if valid_month_cols:
        shipment_volume = df_monthly_vol[valid_month_cols].sum().mean() # Tổng theo tháng, sau đó lấy trung bình
    else:
        shipment_volume = 0
        
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Approved HC", approved_hc)
    col2.metric("Required HC", f"{required_hc:.2f}" if not np.isnan(required_hc) else "0")
    col3.metric("% Workload", f"{workload_pct * 100:.2f}%" if not np.isnan(workload_pct) else "0%")
    col4.metric("Shipment Volume", f"{shipment_volume:,.0f}" if not np.isnan(shipment_volume) else "0")
    
    st.subheader("Mối liên hệ giữa các chỉ số Overview")
    # Biểu đồ kết hợp
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=["Approved HC", "Required HC"], y=[approved_hc, required_hc], name="HC"))
    # Thêm trục y thứ 2 cho Workload và Shipment để dễ nhìn (do chênh lệch scale)
    fig1.add_trace(go.Scatter(x=["% Workload"], y=[workload_pct], mode="markers+text", marker=dict(size=20, color="orange"), name="Workload", text=[f"{workload_pct:.1%}"], yaxis="y2"))
    
    fig1.update_layout(
        yaxis2=dict(title="% Workload", overlaying="y", side="right"),
        barmode='group'
    )
    st.plotly_chart(fig1, use_container_width=True)


elif page == "HC Status":
    st.title("HC Status")
    
    hc_filtered = filter_by_month(df_hc)
    
    # Metrics
    approved_hc = 11
    available_hc = hc_filtered['Available HC'].dropna().mean()
    required_hc = hc_filtered['Required HC'].dropna().mean()
    workload_pct = hc_filtered['% Worload'].dropna().mean() if '% Worload' in hc_filtered.columns else hc_filtered['% Workload'].dropna().mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Approved HC", approved_hc)
    col2.metric("Available HC", f"{available_hc:.2f}" if not np.isnan(available_hc) else "0")
    col3.metric("Required HC", f"{required_hc:.2f}" if not np.isnan(required_hc) else "0")
    col4.metric("% Workload", f"{workload_pct * 100:.2f}%" if not np.isnan(workload_pct) else "0%")
    
    st.subheader("Mối liên hệ giữa các chỉ số HC")
    # Biểu đồ bar chart so sánh các HC
    fig_hc = go.Figure(data=[
        go.Bar(name='HC Metrics', x=['Approved HC', 'Available HC', 'Required HC'], y=[approved_hc, available_hc, required_hc], text=[f"{approved_hc}", f"{available_hc:.1f}", f"{required_hc:.1f}"], textposition='auto')
    ])
    fig_hc.add_trace(go.Scatter(name='% Workload', x=['Approved HC', 'Available HC', 'Required HC'], y=[workload_pct, workload_pct, workload_pct], yaxis='y2', mode='lines+markers'))
    fig_hc.update_layout(yaxis2=dict(overlaying='y', side='right', tickformat='.0%'))
    st.plotly_chart(fig_hc, use_container_width=True)
    
    st.subheader("Trend FTE theo từng tháng và CS PIC")
    cs_filtered = filter_by_month(df_cs_fte_melted)
    if not cs_filtered.empty:
        fig_trend = px.line(cs_filtered, x="Month", y="FTE", color="CS PIC", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho các tháng đã chọn.")
        
    st.subheader("Dữ liệu chi tiết")
    st.markdown("**Bảng HC**")
    st.dataframe(hc_filtered, use_container_width=True, hide_index=True)
    st.markdown("**Bảng CS FTE**")
    valid_cols = ["CS PIC"] + [m for m in selected_months if m in df_cs_fte.columns]
    st.dataframe(df_cs_fte[valid_cols], use_container_width=True, hide_index=True)


elif page == "Monthly Volume":
    st.title("Monthly Volume")
    
    office_filtered = filter_by_month(df_office_fte)
    
    active_cust = office_filtered['Active customer'].dropna().mean()
    ship_vol = office_filtered['Shipment Volume'].dropna().mean()
    
    col1, col2 = st.columns(2)
    col1.metric("Active Customer (Avg)", f"{active_cust:.2f}" if not np.isnan(active_cust) else "0")
    col2.metric("Shipment Volume (Avg)", f"{ship_vol:,.2f}" if not np.isnan(ship_vol) else "0")
    
    st.subheader("Active Customer Trend")
    if not office_filtered.empty:
        fig_cust = px.line(office_filtered, x="Month", y="Active customer", markers=True, text="Active customer")
        fig_cust.update_traces(textposition="top center")
        st.plotly_chart(fig_cust, use_container_width=True)
    
    st.subheader("Shipment Volume Trend")
    if not office_filtered.empty:
        fig_vol = px.bar(office_filtered, x="Month", y="Shipment Volume", text_auto=True)
        st.plotly_chart(fig_vol, use_container_width=True)
        
    st.subheader("Dữ liệu chi tiết")
    st.markdown("**Bảng Office FTE**")
    st.dataframe(office_filtered, use_container_width=True, hide_index=True)
    
    st.markdown("**Bảng Monthly Volume**")
    # Lọc cột tháng của Monthly volume
    vol_cols = ["No", "Customer"] + [m for m in selected_months if m in df_monthly_vol.columns]
    if "Total" in df_monthly_vol.columns:
        vol_cols.append("Total")
    st.dataframe(df_monthly_vol[vol_cols], use_container_width=True, hide_index=True)
