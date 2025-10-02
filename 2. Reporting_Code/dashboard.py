import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# --- Authentication Configuration ---
# Simple username/password combinations
USERS = {
    "admin": "admin123",
    "gaurav": "gaurav123",
    "lawrence": "lawrence123",
    "yiling": "yiling123"
}

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def login_form():
    """Display login form"""
    st.markdown("""
    <div style="max-width: 400px; margin: auto; padding: 2rem; 
                background-color: #f0f2f6; border-radius: 10px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-top: 5rem;">
        <h2 style="text-align: center; color: #1f77b4; margin-bottom: 2rem;">
            🔐 Portfolio Dashboard Login
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("### Please enter your credentials")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            if username in USERS and USERS[username] == password:
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

def logout():
    """Handle user logout"""
    for key in ['authenticated', 'username']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def display_user_info():
    """Display current user info and logout button"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Welcome, {st.session_state.get('username', 'User')}!** 👋")
    with col2:
        if st.button("🚪 Logout", type="secondary"):
            logout()

# --- Page Configuration ---
st.set_page_config(
    page_title="Portfolio Performance Dashboard",
    page_icon="📈",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header { 
        font-size:2.5rem; 
        font-weight:bold; 
        text-align:center; 
        color:#1f77b4; 
        margin-bottom:2rem; 
    }
    .section-header { 
        font-size:1.5rem; 
        font-weight:bold; 
        color:#2e8b57; 
        margin-top:2rem; 
        margin-bottom:1rem; 
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stDataFrame {
        width: 100% !important;
    }
    .stDataFrame > div {
        width: 100% !important;
    }
    .stDataFrame [data-testid="stDataFrameResizeHandle"] {
        display: none;
    }
    .detailed-table-button {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .date-selector {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .user-info {
        background-color: #e8f4fd;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def format_currency(val):
    """Format currency values"""
    if pd.isna(val):
        return "$0"
    return f"${val:,.0f}"

def format_pct(val):
    """Format percentage values"""
    if pd.isna(val):
        return "0.00%"
    return f"{val:.2f}%"

def get_previous_weekday():
    """Get the previous weekday (Monday-Friday) from today"""
    today = datetime.today()
    previous_day = today - timedelta(days=1)
    
    while previous_day.weekday() > 4:
        previous_day = previous_day - timedelta(days=1)
    
    return previous_day.date()

def clean_dataframe_for_display(df):
    """Clean dataframe for Arrow compatibility and remove empty rows"""
    if df.empty:
        return df
    
    df_clean = df.copy()
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.replace('', pd.NA)
    df_clean = df_clean.dropna(how='all')
    
    mask = df_clean.apply(lambda row: row.astype(str).str.strip().eq('').all() or row.isna().all(), axis=1)
    df_clean = df_clean[~mask]
    
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str)
    
    df_clean = df_clean.replace('nan', '')
    
    return df_clean

@st.cache_data
def load_data(today_str):
    """Load data files for the specified date"""
    #ghfm_reporting_dir = "../"         # for running on local
    ghfm_reporting_dir = os.getcwd()    # for running on Streamlit Cloud
    year_str = today_str[:4]
    month_str = today_str[:6]

    ib_mtmpnl_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/IB_Mark-to-Market PnL/")
    ibtradessummary_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Daily Trades/")
    performance_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Performance_History/")
    marketvalue_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Market_Value/")

    pnl_file = os.path.join(ib_mtmpnl_dir, "AssetCategory", year_str, month_str, f"Category_P&L_{today_str}.xlsx")
    perf_file = os.path.join(performance_dir, year_str, month_str, f"Performance_{today_str}.csv")
    mv_file = os.path.join(marketvalue_dir, year_str, month_str, f"MarketValue_{today_str}.csv")
    all_symbol_pnl_file = os.path.join(ib_mtmpnl_dir, "AllSymbols", year_str, month_str, f"AllSymbols_P&L_{today_str}.xlsx")
    trade_file = os.path.join(ibtradessummary_dir, year_str, month_str, f"TradeSummary_{today_str}.csv")

    try:
        pnl_df = pd.read_excel(pnl_file, parse_dates=["Date"])
        perf_df = pd.read_csv(perf_file, parse_dates=["DATE"])
        mv_df = pd.read_csv(mv_file, parse_dates=["Date"])
        all_symbol_pnl_df = pd.read_excel(all_symbol_pnl_file)
        trades_df = pd.read_csv(trade_file)
       
        return perf_df, mv_df, pnl_df, all_symbol_pnl_df, trades_df
    except FileNotFoundError:
        st.error(f"Data files for {today_str} not found.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_performance_tables(selected_datetime, perf_df, mv_df, pnl_df):
    """Create all performance tables and metrics"""
    asset_classes = [c.replace(" MarketValue", "") for c in mv_df.columns if "MarketValue" in c]
    
    selected_perf = perf_df[perf_df["DATE"] == selected_datetime].iloc[0]
    selected_mv = mv_df[mv_df["Date"] == selected_datetime].iloc[0]
    selected_pnl = pnl_df[pnl_df["Date"] == selected_datetime].iloc[0]

    overall_portfolio = pd.DataFrame({
        "Date": [selected_perf["DATE"].date()],
        "NAV (USD)": [format_currency(selected_perf["NAV (USD)"])],
        "Daily Return": [format_pct(selected_perf["Daily Return"])],
        "WTD Return": [format_pct(selected_perf["Weekly Return"])],
        "MTD Return": [format_pct(selected_perf["MTD %"])],
        "YTD Return": [format_pct(selected_perf["YTD ROR%"])]
    })

    key_metrics = pd.DataFrame({
        "1-year Return": [format_pct(selected_perf["252 Days Return"])],
        "1-year Volatility": [format_pct(selected_perf['Trailing 252D Annualised Volatility']*100)],
        "1-year Sharpe Ratio": [f"{selected_perf['Trailing 252D Sharpe']:.3f}"],
        "1-year Sortino Ratio": [f"{selected_perf['Trailing 252D Sortino']:.3f}"],
        "95% Value-at-Risk": [format_pct(selected_perf['Value at Risk 95%(252days)']*100)],
        "99% Value-at-Risk": [format_pct(selected_perf['Value at Risk 99%(252days)']*100)]
    })

    total_mv = sum(selected_mv[f"{a} MarketValue"] for a in asset_classes)
    total_daily_pnl = sum(selected_pnl[f"{a} MTM"] for a in asset_classes)
    total_daily_return = sum(selected_pnl[f"{a} Return"] for a in asset_classes)
    
    performance_data = {
        'Metric': ['No of Tickers', 'Market Value USD', 'Market Value %', 'Daily Return USD', 'Daily Return %']
    }
    
    total_tickers = 0
    for asset_class in asset_classes:
        mv_value = selected_mv[f"{asset_class} MarketValue"]
        daily_pnl = selected_pnl[f"{asset_class} MTM"]
        mv_pct = (mv_value / total_mv * 100) if total_mv != 0 else 0
        daily_return_pct = selected_pnl[f"{asset_class} Return"]
        
        count_col = f"{asset_class} Count"
        ticker_count = selected_mv.get(count_col, 0)
        if pd.isna(ticker_count):
            ticker_count = 0
        total_tickers += int(ticker_count)
        
        performance_data[asset_class] = [
            str(int(ticker_count)),
            format_currency(mv_value),
            f"{mv_pct:.2f}%",
            format_currency(daily_pnl),
            f"{daily_return_pct*100:.2f}%"
        ]
    
    performance_data['Total'] = [
        str(total_tickers),
        format_currency(total_mv),
        "100.00%",
        format_currency(total_daily_pnl),
        f"{total_daily_return*100:.2f}%"
    ]
    
    performance_by_asset_class = pd.DataFrame(performance_data)

    pnl_df["Year"] = pnl_df["Date"].dt.year
    pnl_df["Month"] = pnl_df["Date"].dt.month
    current_year = selected_datetime.year
    months = range(1, 13)
    monthly_attrib_usd = pd.DataFrame(0.0, index=months, columns=asset_classes)
    
    for m in months:
        month_data = pnl_df[(pnl_df["Year"] == current_year) & (pnl_df["Month"] == m)]
        if not month_data.empty:
            monthly_attrib_usd.loc[m, asset_classes] = month_data[[f"{a} MTM" for a in asset_classes]].sum().values
    
    monthly_attrib_usd.index = [datetime(current_year, m, 1).strftime("%b %y") for m in months]
    monthly_attrib_usd.loc[f"FY{current_year}"] = monthly_attrib_usd.sum()

    return overall_portfolio, key_metrics, performance_by_asset_class, monthly_attrib_usd, asset_classes

def create_plotly_charts(performance_by_asset_class, monthly_attrib_usd, asset_classes, perf_df, selected_datetime):
    """Create all Plotly charts"""
    mv_row = performance_by_asset_class[performance_by_asset_class['Metric'] == 'Market Value USD']
    mv_values = []
    for asset_class in asset_classes:
        mv_str = mv_row[asset_class].values[0]
        mv_val = float(mv_str.replace('$', '').replace(',', ''))
        mv_values.append(mv_val)
    
    colors = ['green' if x >= 0 else 'red' for x in mv_values]
    fig1 = go.Figure(go.Bar(
        y=asset_classes, x=mv_values, orientation='h', marker_color=colors,
        text=[format_currency(x) for x in mv_values], textposition='outside'
    ))
    fig1.update_layout(title="Portfolio Market Value by Asset Category", xaxis_title="Market Value USD", height=400)

    current_year = selected_datetime.year
    ytd_data = perf_df[perf_df["DATE"].dt.year == current_year]
    fig2 = go.Figure(go.Scatter(x=ytd_data["DATE"], y=ytd_data["YTD ROR%"], mode='lines', line=dict(color='blue', width=2)))
    fig2.update_layout(title=f"YTD Cumulative Return ({current_year})", xaxis_title="Date", yaxis_title="YTD Return (%)", height=400)

    fig3 = go.Figure(go.Scatter(x=perf_df["DATE"], y=perf_df["LTD ROR%"], mode='lines', line=dict(color='green', width=2)))
    fig3.update_layout(title="Inception-to-Date Cumulative Return", xaxis_title="Date", yaxis_title="ITD Return (%)", height=400)

    month_str = selected_datetime.strftime("%b %y")
    if month_str in monthly_attrib_usd.index:
        monthly_pnl = monthly_attrib_usd.loc[month_str, asset_classes].values
        colors = ['green' if x >= 0 else 'red' for x in monthly_pnl]
        
        max_val = max(monthly_pnl) if len(monthly_pnl) > 0 else 1000
        min_val = min(monthly_pnl) if len(monthly_pnl) > 0 else -1000
        y_range_padding = max(abs(max_val), abs(min_val)) * 0.15
        
        fig4 = go.Figure(go.Bar(
            x=asset_classes, 
            y=monthly_pnl, 
            marker_color=colors, 
            text=[format_currency(x) for x in monthly_pnl], 
            textposition='outside',
            textfont=dict(size=10)
        ))
        fig4.update_layout(
            title=f"Monthly Attribution to PnL ({month_str})", 
            xaxis_title="Asset Category", 
            yaxis_title="PnL USD", 
            height=550,
            margin=dict(t=100, b=60, l=60, r=60),
            yaxis=dict(range=[min_val - y_range_padding, max_val + y_range_padding])
        )
    else:
        fig4 = go.Figure()
        fig4.update_layout(title="No Monthly PnL Data", height=550)

    yearly_pnl = monthly_attrib_usd.loc[f"FY{current_year}", asset_classes].values
    colors = ['green' if x >= 0 else 'red' for x in yearly_pnl]
    
    max_val = max(yearly_pnl) if len(yearly_pnl) > 0 else 1000
    min_val = min(yearly_pnl) if len(yearly_pnl) > 0 else -1000
    y_range_padding = max(abs(max_val), abs(min_val)) * 0.15
    
    fig5 = go.Figure(go.Bar(
        x=asset_classes, 
        y=yearly_pnl, 
        marker_color=colors, 
        text=[format_currency(x) for x in yearly_pnl], 
        textposition='outside',
        textfont=dict(size=10)
    ))
    fig5.update_layout(
        title=f"Yearly Attribution to PnL ({current_year})", 
        xaxis_title="Asset Category", 
        yaxis_title="PnL USD", 
        height=550,
        margin=dict(t=100, b=60, l=60, r=60),
        yaxis=dict(range=[min_val - y_range_padding, max_val + y_range_padding])
    )

    return fig1, fig2, fig3, fig4, fig5

def main():
    # Check authentication first
    if not check_authentication():
        login_form()
        return
    
    # Display user info and logout option
    st.markdown('<div class="user-info">', unsafe_allow_html=True)
    display_user_info()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">📈 Portfolio Performance Dashboard</h1>', unsafe_allow_html=True)
    
    # Date selector in main page - centered
    st.markdown('<div class="date-selector">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        default_date = get_previous_weekday()
        selected_date = st.date_input("📅 Select Date", default_date)
        selected_datetime = pd.to_datetime(selected_date)
        today_str = selected_datetime.strftime("%Y%m%d")
    st.markdown('</div>', unsafe_allow_html=True)

    # Initialize session state for button toggles
    if 'show_all_symbols' not in st.session_state:
        st.session_state.show_all_symbols = False
    if 'show_top20_symbols' not in st.session_state:
        st.session_state.show_top20_symbols = False
    if 'show_pnl_daily' not in st.session_state:
        st.session_state.show_pnl_daily = False

    # Load data dynamically
    perf_df, mv_df, pnl_df, all_symbol_pnl_df, trades_df = load_data(today_str)
    if perf_df.empty or mv_df.empty or pnl_df.empty:
        st.warning("No data available for this date. Please select a different date.")
        return

    # Create tables and get metrics
    overall_portfolio, key_metrics, performance_by_asset_class, monthly_attrib_usd, asset_classes = create_performance_tables(selected_datetime, perf_df, mv_df, pnl_df)

    # Overall Portfolio Summary with improved metrics display
    st.markdown('<h3 class="section-header">📊 Overall Portfolio Summary</h3>', unsafe_allow_html=True)
    
    # Display key metrics in columns
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Date", overall_portfolio.iloc[0]["Date"].strftime("%Y-%m-%d"))
    col2.metric("NAV (USD)", overall_portfolio.iloc[0]["NAV (USD)"])
    col3.metric("Daily Return", overall_portfolio.iloc[0]["Daily Return"])
    col4.metric("WTD Return", overall_portfolio.iloc[0]["WTD Return"])
    col5.metric("MTD Return", overall_portfolio.iloc[0]["MTD Return"])
    col6.metric("YTD Return", overall_portfolio.iloc[0]["YTD Return"])

    # Key Performance Metrics
    st.markdown('<h3 class="section-header">🎯 Key Performance Metrics</h3>', unsafe_allow_html=True)
    st.dataframe(key_metrics, width='stretch', hide_index=True)

    st.markdown(
        '<p style="font-size: 0.85em; color: #666; font-style: italic; margin-top: 8px;">'
        '📝 <strong>Note:</strong> All metrics are calculated based on trading days, not calendar days. '
        '1-year is based on 252 trading days per year.</p>', 
        unsafe_allow_html=True
    )

    # Performance by Asset Class
    st.markdown('<h3 class="section-header">🏦 Performance by Asset Class</h3>', unsafe_allow_html=True)
    st.dataframe(
        performance_by_asset_class.set_index('Metric'), 
        width='stretch'
    )

    # Top 20 symbols by Market Value view
    if not all_symbol_pnl_df.empty:
        button_text_top20 = f"Hide List of Top 20 Symbols by Market Value as on {selected_date}" if st.session_state.show_top20_symbols else f"View List of Top 20 Symbols by Market Value as on {selected_date}"
        
        if st.button(button_text_top20, key="top20_symbols_btn"):
            st.session_state.show_top20_symbols = not st.session_state.show_top20_symbols
            st.rerun()
        
        if st.session_state.show_top20_symbols:
            st.markdown('<h3 class="section-header">🏆 Top 20 Symbols by Market Value</h3>', unsafe_allow_html=True)
            top20_df = all_symbol_pnl_df.nlargest(20, 'Market Value USD')
            top20_clean = clean_dataframe_for_display(top20_df)
            st.dataframe(top20_clean, width='stretch', height=500, hide_index=True)

    # Detailed symbols view
    if not all_symbol_pnl_df.empty:
        button_text = f"Hide performance for all symbols for {selected_date}" if st.session_state.show_all_symbols else f"View performance for all symbols for {selected_date}"
        
        if st.button(button_text, key="all_symbols_btn"):
            st.session_state.show_all_symbols = not st.session_state.show_all_symbols
            st.rerun()
        
        if st.session_state.show_all_symbols:
            st.markdown('<h3 class="section-header">📋 Detailed Performance for All Symbols</h3>', unsafe_allow_html=True)
            all_symbols_clean = clean_dataframe_for_display(all_symbol_pnl_df)
            st.dataframe(all_symbols_clean, width='stretch', height=500, hide_index=True)

    # Charts
    st.markdown('<h3 class="section-header">📈 Performance Charts</h3>', unsafe_allow_html=True)
    fig1, fig2, fig3, fig4, fig5 = create_plotly_charts(performance_by_asset_class, monthly_attrib_usd, asset_classes, perf_df, selected_datetime)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Market Value", "YTD Returns", "ITD Returns", "Monthly PnL", "Yearly PnL"])
    with tab1:
        st.plotly_chart(fig1, use_container_width=True)
    with tab2:
        st.plotly_chart(fig2, use_container_width=True)
    with tab3:
        st.plotly_chart(fig3, use_container_width=True)
    with tab4:
        st.plotly_chart(fig4, use_container_width=True)
    with tab5:
        st.plotly_chart(fig5, use_container_width=True)

    # Monthly/Yearly Attribution
    st.markdown('<h3 class="section-header">📋 Monthly & Yearly Attribution to PnL</h3>', unsafe_allow_html=True)

    monthly_attrib_usd_with_total = monthly_attrib_usd.copy()
    monthly_attrib_usd_with_total['Total'] = monthly_attrib_usd_with_total.sum(axis=1)

    monthly_attrib_usd_formatted = monthly_attrib_usd_with_total.copy()
    for col in monthly_attrib_usd_formatted.columns:
        monthly_attrib_usd_formatted[col] = monthly_attrib_usd_formatted[col].apply(format_currency)
    st.dataframe(monthly_attrib_usd_formatted, width='stretch', height=500)

    # PnL History
    button_text_pnl = "Hide PnL History of Asset Categories Day by Day" if st.session_state.show_pnl_daily else "View PnL History of Asset Categories Day by Day"
    
    if st.button(button_text_pnl, key="pnl_daily_btn"):
        st.session_state.show_pnl_daily = not st.session_state.show_pnl_daily
        st.rerun()
    
    if st.session_state.show_pnl_daily:
        st.markdown('<h3 class="section-header">📈 PnL History of Asset Categories Day by Day</h3>', unsafe_allow_html=True)
        pnl_display_df = pnl_df.copy()
        numeric_columns = [col for col in pnl_display_df.columns if col not in ['Date', 'Year', 'Month']]
        for col in numeric_columns:
            if 'MTM' in col or 'PnL' in col:
                pnl_display_df[col] = pnl_display_df[col].apply(format_currency)
            elif 'Return' in col:
                pnl_display_df[col] = (pnl_display_df[col] * 100).apply(lambda x: f"{x:.2f}%")
        pnl_display_df = pnl_display_df.drop(columns=['Year', 'Month'])
        pnl_display_df['Date'] = pnl_display_df['Date'].dt.date
        st.dataframe(pnl_display_df, width='stretch', height=600, hide_index=True)

    # Executed Trades Section
    st.markdown(f'<h3 class="section-header">💼 Executed Trades on {selected_date}</h3>', unsafe_allow_html=True)
    if not trades_df.empty:
        trades_clean = clean_dataframe_for_display(trades_df)
        st.dataframe(trades_clean, width='stretch', height=500, hide_index=True)
    else:
        st.info(f"No trade data available for {selected_date}")

    # Footer
    st.markdown("---")
    st.markdown(f"*Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()