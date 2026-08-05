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
# Custom CSS giao diện
st.markdown("""
    <style>
    /* 1. Bao trùm màu nền xám nhạt cho toàn bộ khung ứng dụng & header trên cùng */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #f4f6f9 !important;
    }
    
    /* 2. Loại bỏ padding đỉnh giúp trang bên phải đẩy cao lên sát mép trên bằng sidebar */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 3. Thanh Sidebar (khu vực lựa chọn trang & tháng) màu Xanh tím */
    [data-testid="stSidebar"] {
        background-color: #4D44B5 !important;
    }
    
    /* Đổi màu chữ và icon trong Sidebar thành màu trắng */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Style cho các tag chọn tháng trong Multiselect */
    span[data-baseweb="tag"] {
        background-color: #1e3e62 !important;
        color: #ffffff !important;
    }
    
    /* 4. Thu nhỏ kích thước tiêu đề */
    h1, .stTitle {
        font-size: 18px !important;
        color: #0b192c !important;
        font-weight: 700 !important;
        margin-top: 0px !important;
        padding-top: 0px !important;
        padding-bottom: 2px !important;
    }
    
    h2, h3, .stHeader {
        font-size: 15px !important;
        color: #1e3e62 !important;
        font-weight: 600 !important;
        margin-top: 5px !important;
        padding-bottom: 2px !important;
    }
    
    /* 5. Vạch phân cách & Tạo khoảng cách 3-4 dòng trống (50px) bên dưới tiêu đề chính */
    hr {
        margin-top: 1px !important;
        margin-bottom: 50px !important;
        border-color: #cbd5e1 !important;
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = Path("FTE dashboard data.xlsx")

st.sidebar.title("📊 VOLUME & FTE")

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
st.sidebar.header("Filter")
selected_months = st.sidebar.multiselect(
    "By month",
    options=months_list,
    default=months_list
)

# Chuyển đổi dữ liệu CS FTE từ dạng cột sang dòng để dễ vẽ biểu đồ trend
df_cs_fte_melted = df_cs_fte.melt(id_vars=["CS PIC"], var_name="Month", value_name="FTE")
df_cs_fte_melted = df_cs_fte_melted[df_cs_fte_melted['FTE'].notna()]

# CHỌN TRANG
page = st.sidebar.radio("Select data", ["Overview", "HC Status", "Monthly Volume"])

# HÀM LỌC DỮ LIỆU CHUNG
def filter_by_month(df, month_col="Month"):
    if not selected_months:
        return df.iloc[0:0] # Trả về df rỗng nếu không chọn tháng nào
    return df[df[month_col].astype(str).isin(selected_months)].copy()

# HÀM TẠO CARD THÔNG TIN (Số ở trên, Chữ ở dưới, ô xám bo tròn)
def custom_metric_card(value, label):
    st.markdown(f"""
    <div style="
        background-color: #FFFFFF;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 18px 12px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        margin-bottom: 15px;
    ">
        <div style="
            font-size: 32px;
            font-weight: 700;
            color: #F97316;
            line-height: 1.2;
        ">{value}</div>
        <div style="
            font-size: 14px;
            font-weight: 500;
            color: #64748b;
            margin-top: 6px;
        ">{label}</div>
    </div>
    """, unsafe_allow_html=True)

# TIÊU ĐỀ CHUNG HIỂN THỊ TRÊN TẤT CẢ CÁC TRANG
st.title("CSHAD - VOLUME & FTE DASHBOARD")
st.divider()

if page == "Overview":
    st.title("VOLUME & FTE OVERVIEW")
    
    # Lọc dữ liệu sheet HC
    hc_filtered = filter_by_month(df_hc)
    
    shipment_col = 'Shipment Volume'
    
   # Tính toán Metrics
    approved_hc = 11
    required_hc = hc_filtered['Required HC'].dropna().mean() if 'Required HC' in hc_filtered.columns else 0
    workload_pct = hc_filtered['% Worload'].dropna().mean() if '% Worload' in hc_filtered.columns else (hc_filtered['% Workload'].dropna().mean() if '% Workload' in hc_filtered.columns else 0)
    
    if shipment_col and shipment_col in hc_filtered.columns:
        shipment_volume = hc_filtered[shipment_col].dropna().mean()
    else:
        shipment_volume = 0
        
    val_approved = f"{approved_hc}"
    val_required = f"{required_hc:.2f}" if not np.isnan(required_hc) else "0"
    val_workload = f"{workload_pct * 100:.2f}%" if not np.isnan(workload_pct) else "0%"
    val_shipment = f"{shipment_volume:,.0f}" if not np.isnan(shipment_volume) else "0"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        custom_metric_card(val_approved, "Approved HC")
    with col2:
        custom_metric_card(val_required, "Required HC")
    with col3:
        custom_metric_card(val_workload, "% Workload")
    with col4:
        custom_metric_card(val_shipment, "Shipment Volume (Avg)")
    
    st.subheader("Mối liên hệ giữa Shipment Volume, Required HC và Approved HC theo tháng")
    
    if not hc_filtered.empty:
        fig1 = go.Figure()

        # 1. Biểu đồ Cột: Shipment Volume từ Cột G sheet HC (Trục Y bên trái)
        if shipment_col and shipment_col in hc_filtered.columns:
            fig1.add_trace(go.Bar(
                x=hc_filtered['Month'],
                y=hc_filtered[shipment_col],
                name='Shipment Volume',
                marker_color='#93c5fd',
                text=hc_filtered[shipment_col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else ""),
                textposition='auto',
                yaxis='y'
            ))

        # 2. Biểu đồ Đường: Required HC từ Cột D sheet HC (Trục Y bên phải)
        if 'Required HC' in hc_filtered.columns:
            fig1.add_trace(go.Scatter(
                x=hc_filtered['Month'],
                y=hc_filtered['Required HC'],
                mode='lines+markers+text',
                name='Required HC',
                line=dict(color='#ef4444', width=2.5),
                text=hc_filtered['Required HC'].round(1),
                textposition='top center',
                yaxis='y2'
            ))

        # 3. Biểu đồ Đường: Approved HC từ Cột B sheet HC (Trục Y bên phải)
        if 'Approved HC' in hc_filtered.columns:
            fig1.add_trace(go.Scatter(
                x=hc_filtered['Month'],
                y=hc_filtered['Approved HC'],
                mode='lines+markers+text',
                name='Approved HC',
                line=dict(color='#1e3e62', width=2, dash='dash'),
                text=hc_filtered['Approved HC'],
                textposition='top center',
                yaxis='y2'
            ))

        fig1.update_layout(
            xaxis=dict(title="Tháng"),
            yaxis=dict(title="Shipment Volume", showgrid=False),
            yaxis2=dict(title="Headcount (HC)", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=20, l=20, r=20),
            hovermode="x unified"
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho các tháng đã chọn.")


elif page == "HC Status":
    st.title("HC STATUS")
    
    hc_filtered = filter_by_month(df_hc)
    
    # Metrics
    approved_hc = 11
    required_hc = hc_filtered['Required HC'].dropna().mean()
    workload_pct = hc_filtered['% Worload'].dropna().mean() if '% Worload' in hc_filtered.columns else hc_filtered['% Workload'].dropna().mean()
    available_hc = hc_filtered['Available HC'].dropna().mean()
    
    val_approved = f"{approved_hc}"
    val_available = f"{available_hc:.2f}" if not np.isnan(available_hc) else "0"
    val_required = f"{required_hc:.2f}" if not np.isnan(required_hc) else "0"
    val_workload = f"{workload_pct * 100:.2f}%" if not np.isnan(workload_pct) else "0%"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        custom_metric_card(val_approved, "Approved HC")
    with col2:
        custom_metric_card(val_available, "Available HC")
    with col3:
        custom_metric_card(val_required, "Required HC")
    with col4:
        custom_metric_card(val_workload, "% Workload")
    
    st.subheader("Mối liên hệ & khoảng Gap giữa Available HC vs Required HC theo tháng")
    if not hc_filtered.empty:
        fig_hc = go.Figure()

        # Đường 1: Required HC
        fig_hc.add_trace(go.Scatter(
            x=hc_filtered['Month'],
            y=hc_filtered['Required HC'],
            mode='lines+markers+text',
            name='Required HC',
            text=hc_filtered['Required HC'].round(1),
            textposition='top center',
            line=dict(color='#ef4444', width=2.5)
        ))

        # Đường 2: Available HC + Fill màu khoảng Gap tới Required HC
        fig_hc.add_trace(go.Scatter(
            x=hc_filtered['Month'],
            y=hc_filtered['Available HC'],
            mode='lines+markers+text',
            name='Available HC',
            text=hc_filtered['Available HC'].round(1),
            textposition='bottom center',
            line=dict(color='#22c55e', width=2.5),
            fill='tonexty',
            fillcolor='rgba(239, 68, 68, 0.15)'
        ))

        # Đường 3: Approved HC (Nét đứt)
        fig_hc.add_trace(go.Scatter(
            x=hc_filtered['Month'],
            y=hc_filtered['Approved HC'],
            mode='lines+markers+text',
            name='Approved HC',
            text=hc_filtered['Approved HC'],
            textposition='top center',
            line=dict(color='#3b82f6', width=2, dash='dash')
        ))

        fig_hc.update_layout(
            xaxis_title="Tháng",
            yaxis_title="Headcount (HC)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_hc, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho các tháng đã chọn.")
    
    st.subheader("Trend FTE theo từng tháng và CS PIC")
    cs_filtered = filter_by_month(df_cs_fte_melted)
    if not cs_filtered.empty:
        fig_trend = px.line(cs_filtered, x="Month", y="FTE", color="CS PIC", markers=True)
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=20, r=20))
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
    st.title("MONTHLY VOLUME")
    
    office_filtered = filter_by_month(df_office_fte)
    
    active_cust = office_filtered['Active customer'].dropna().mean()
    ship_vol = office_filtered['Shipment Volume'].dropna().mean()
    
    val_cust = f"{active_cust:.2f}" if not np.isnan(active_cust) else "0"
    val_ship = f"{ship_vol:,.2f}" if not np.isnan(ship_vol) else "0"

    col1, col2 = st.columns(2)
    with col1:
        custom_metric_card(val_cust, "Active Customer (Avg)")
    with col2:
        custom_metric_card(val_ship, "Shipment Volume (Avg)")
    
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
    vol_cols = ["No", "Customer"] + [m for m in selected_months if m in df_monthly_vol.columns]
    if "Total" in df_monthly_vol.columns:
        vol_cols.append("Total")
    st.dataframe(df_monthly_vol[vol_cols], use_container_width=True, hide_index=True)
