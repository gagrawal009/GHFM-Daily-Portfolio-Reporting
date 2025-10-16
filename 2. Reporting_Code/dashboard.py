import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import glob
import pytz


# --- Authentication Configuration ---
# Simple username/password combinations
USERS = {
    "admin": "admin123",
    "gaurav": "gaurav123",
    "lawrence": "lawrence123",
    "yiling": "yiling123"
}

ghfm_reporting_dir = os.getcwd()

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

# --- Top 10 Symbols Feature Functions ---
def get_all_symbols_files_for_period(period_type, period_value, year=None):
    """
    Get all AllSymbols P&L files for a given period
    
    Args:
        period_type: 'month' or 'year'
        period_value: Month (1-12) or Year (e.g., 2025)
        year: Year (required if period_type is 'month')
    
    Returns:
        List of file paths matching the period
    """
    ib_mtmpnl_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/IB_Mark-to-Market PnL/AllSymbols/")
    
    if period_type == 'month':
        if year is None:
            raise ValueError("Year must be provided for month period")
        month_str = f"{year}{period_value:02d}"
        search_pattern = os.path.join(ib_mtmpnl_dir, str(year), month_str, "AllSymbols_P&L_*.xlsx")
    elif period_type == 'year':
        search_pattern = os.path.join(ib_mtmpnl_dir, str(period_value), "*", "AllSymbols_P&L_*.xlsx")
    else:
        raise ValueError("period_type must be 'month' or 'year'")
    
    files = glob.glob(search_pattern)
    return files

def load_and_concatenate_symbols_data(file_list):
    """
    Load and concatenate all symbol P&L files
    
    Args:
        file_list: List of file paths to load
    
    Returns:
        Concatenated DataFrame with all symbol data
    """
    if not file_list:
        return pd.DataFrame()
    
    dfs = []
    for file in file_list:
        try:
            df = pd.read_excel(file)
            dfs.append(df)
        except Exception as e:
            st.warning(f"Error reading {file}: {str(e)}")
            continue
    
    if not dfs:
        return pd.DataFrame()
    
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df

def get_top_symbols_for_period(period_type, period_value, category=None, year=None, top_n=10):
    """
    Get top N symbols by MTM PnL for a specific period and category
    
    Args:
        period_type: 'month' or 'year'
        period_value: Month (1-12) or Year (e.g., 2025)
        category: Asset category (e.g., 'Equity', 'Fixed Income') or None for total
        year: Year (required if period_type is 'month')
        top_n: Number of top symbols to return (default: 10)
    
    Returns:
        DataFrame with top symbols sorted by MTM P&L (descending by absolute value)
    """
    files = get_all_symbols_files_for_period(period_type, period_value, year)
    
    if not files:
        return pd.DataFrame()
    
    combined_df = load_and_concatenate_symbols_data(files)
    
    if combined_df.empty:
        return pd.DataFrame()
    
    if category and category != 'Total':
        combined_df = combined_df[combined_df['AssetCategory'] == category]
    
    if combined_df.empty:
        return pd.DataFrame()
    
    symbols_grouped = combined_df.groupby('Symbol').agg({
        'MTM P&L': 'sum',
        'AssetCategory': 'first'
    }).reset_index()
    
    symbols_grouped = symbols_grouped.sort_values('MTM P&L', ascending=False).head(top_n)
    
    return symbols_grouped

def display_top_symbols_modal(symbols_df, period_display, category_display):
    """
    Display top symbols in Streamlit
    
    Args:
        symbols_df: DataFrame with top symbols
        period_display: String to display the period (e.g., "Sep 25", "FY2025")
        category_display: String to display the category (e.g., "Equity", "Total")
    """
    if symbols_df.empty:
        st.warning(f"No data found for {category_display} in {period_display}")
        return
    
    display_df = symbols_df.copy()
    if 'MTM P&L' in display_df.columns:
        display_df['MTM P&L'] = display_df['MTM P&L'].apply(lambda x: f"${x:,.2f}")
    if 'Current Price' in display_df.columns:
        display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"${x:,.2f}")
    if 'Market Value USD' in display_df.columns:
        display_df['Market Value USD'] = display_df['Market Value USD'].apply(lambda x: f"${x:,.2f}")
    
    st.markdown(f"### Top 10 {category_display} Symbols by PnL - {period_display}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

@st.cache_data
def load_data(today_str):
    """Load data files for the specified date"""
    
    year_str = today_str[:4]
    month_str = today_str[:6]

    ib_mtmpnl_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/IB_Mark-to-Market PnL/")
    ibtradessummary_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Daily Trades/")
    performance_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Performance_History/")
    marketvalue_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Market_Value/MV_AssetCategory")
    marketvalue_currency_dir = os.path.join(ghfm_reporting_dir, "1. Reporting_Data/Market_Value/MV_AssetCurrency")

    pnl_file = os.path.join(ib_mtmpnl_dir, "AssetCategory", year_str, month_str, f"Category_P&L_{today_str}.xlsx")
    perf_file = os.path.join(performance_dir, year_str, month_str, f"Performance_{today_str}.csv")
    mv_file = os.path.join(marketvalue_dir, year_str, month_str, f"MarketValue_{today_str}.csv")
    all_symbol_pnl_file = os.path.join(ib_mtmpnl_dir, "AllSymbols", year_str, month_str, f"AllSymbols_P&L_{today_str}.xlsx")
    trade_file = os.path.join(ibtradessummary_dir, year_str, month_str, f"TradeSummary_{today_str}.csv")
    pnl_currency_file = os.path.join(ib_mtmpnl_dir, "AssetCurrency", year_str, month_str, f"Currency_P&L_{today_str}.xlsx")
    mv_currency_file = os.path.join(marketvalue_currency_dir, year_str, month_str, f"MarketValue_Currency_{today_str}.csv")

    try:
        pnl_df = pd.read_excel(pnl_file, parse_dates=["Date"])
        perf_df = pd.read_csv(perf_file, parse_dates=["DATE"])
        mv_df = pd.read_csv(mv_file, parse_dates=["Date"])
        all_symbol_pnl_df = pd.read_excel(all_symbol_pnl_file)
        trades_df = pd.read_csv(trade_file)
        pnl_currency_df = pd.read_excel(pnl_currency_file, parse_dates=["Date"])
        mv_currency_df = pd.read_csv(mv_currency_file, parse_dates=["Date"])
       
        return perf_df, mv_df, pnl_df, all_symbol_pnl_df, trades_df, pnl_currency_df, mv_currency_df
    except FileNotFoundError as e:
        st.error(f"Data files for {today_str} not found. Error: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_performance_tables(selected_datetime, perf_df, mv_df, pnl_df, mv_currency_df, pnl_currency_df):
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

    # Create Performance by Geographical Location table
    countries = [c.replace(" MarketValueUSD", "") for c in mv_currency_df.columns if "MarketValueUSD" in c]
    
    selected_mv_currency = mv_currency_df[mv_currency_df["Date"] == selected_datetime].iloc[0]
    selected_pnl_currency = pnl_currency_df[pnl_currency_df["Date"] == selected_datetime].iloc[0]
    
    # Filter out countries with zero count
    countries_to_keep = []
    for country in countries:
        count_col = f"{country} Count"
        if count_col in selected_mv_currency.index:
            count_value = selected_mv_currency[count_col]
            if not pd.isna(count_value) and count_value > 0:
                countries_to_keep.append(country)
        else:
            # If count column doesn't exist, keep the country
            countries_to_keep.append(country)
    
    countries = countries_to_keep

    total_mv_geo = sum(selected_mv_currency[f"{c} MarketValueUSD"] for c in countries)
    total_daily_pnl_geo = sum(selected_pnl_currency[f"{c} MTM"] for c in countries)
    total_daily_return_geo = sum(selected_pnl_currency[f"{c} Return"] for c in countries)
    
    performance_geo_data = {
        'Metric': ['No of Tickers', 'Market Value USD', 'Market Value %', 'Daily Return USD', 'Daily Return %']
    }
    
    total_tickers_geo = 0
    for country in countries:
        mv_value_geo = selected_mv_currency[f"{country} MarketValueUSD"]
        daily_pnl_geo = selected_pnl_currency[f"{country} MTM"]
        mv_pct_geo = (mv_value_geo / total_mv_geo * 100) if total_mv_geo != 0 else 0
        daily_return_pct_geo = selected_pnl_currency[f"{country} Return"]
        
        count_col_geo = f"{country} Count"
        ticker_count_geo = selected_mv_currency.get(count_col_geo, 0)
        if pd.isna(ticker_count_geo):
            ticker_count_geo = 0
        total_tickers_geo += int(ticker_count_geo)
        
        performance_geo_data[country] = [
            str(int(ticker_count_geo)),
            format_currency(mv_value_geo),
            f"{mv_pct_geo:.2f}%",
            format_currency(daily_pnl_geo),
            f"{daily_return_pct_geo*100:.2f}%"
        ]
    
    performance_geo_data['Total'] = [
        str(total_tickers_geo),
        format_currency(total_mv_geo),
        "100.00%",
        format_currency(total_daily_pnl_geo),
        f"{total_daily_return_geo*100:.2f}%"
    ]
    
    performance_by_geography = pd.DataFrame(performance_geo_data)

    pnl_df["Year"] = pnl_df["Date"].dt.year
    pnl_df["Month"] = pnl_df["Date"].dt.month
    current_year = selected_datetime.year
    months = range(1, 13)
    all_rows = []
    monthly_attrib_usd = pd.DataFrame(0.0, index=months, columns=asset_classes)
    
    for m in months:
        month_data = pnl_df[(pnl_df["Year"] == current_year) & (pnl_df["Month"] == m)]
        if not month_data.empty:
            monthly_attrib_usd.loc[m, asset_classes] = month_data[[f"{a} MTM" for a in asset_classes]].sum().values
    
    monthly_attrib_usd.index = [datetime(current_year, m, 1).strftime("%b %y") for m in months]

    all_rows.append(monthly_attrib_usd)

    # --- (2) Add FY rows for all years (including current year) ---
    for y in sorted(pnl_df["Year"].unique(), reverse=True):
        year_data = pnl_df[pnl_df["Year"] == y]
        if not year_data.empty:
            fy_row = pd.DataFrame(
                [year_data[[f"{a} MTM" for a in asset_classes]].sum().values],
                index=[f"FY{y}"],
                columns=asset_classes,
            )
            all_rows.append(fy_row)
    final_attrib_usd = pd.concat(all_rows)

    return overall_portfolio, key_metrics, performance_by_asset_class, performance_by_geography, final_attrib_usd, asset_classes

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
    if 'show_top10_symbols' not in st.session_state:
        st.session_state.show_top10_symbols = False

    # Load data dynamically
    perf_df, mv_df, pnl_df, all_symbol_pnl_df, trades_df, pnl_currency_df, mv_currency_df = load_data(today_str)
    if perf_df.empty or mv_df.empty or pnl_df.empty:
        st.warning("No data available for this date. Please select a different date.")
        return

    # Create tables and get metrics
    overall_portfolio, key_metrics, performance_by_asset_class, performance_by_geography, monthly_attrib_usd, asset_classes = create_performance_tables(selected_datetime, perf_df, mv_df, pnl_df, mv_currency_df, pnl_currency_df)

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
    st.dataframe(key_metrics, use_container_width=True, hide_index=True)

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
       use_container_width=True
    )

    # Performance by Geographical Location
    st.markdown('<h3 class="section-header">🌍 Performance by Geographical Location</h3>', unsafe_allow_html=True)
    st.dataframe(
        performance_by_geography.set_index('Metric'), 
       use_container_width=True
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
            st.dataframe(top20_clean,use_container_width=True, height=500, hide_index=True)

    # Detailed symbols view
    if not all_symbol_pnl_df.empty:
        button_text = f"Hide performance for all symbols for {selected_date}" if st.session_state.show_all_symbols else f"View performance for all symbols for {selected_date}"
        
        if st.button(button_text, key="all_symbols_btn"):
            st.session_state.show_all_symbols = not st.session_state.show_all_symbols
            st.rerun()
        
        if st.session_state.show_all_symbols:
            st.markdown('<h3 class="section-header">📋 Detailed Performance for All Symbols</h3>', unsafe_allow_html=True)
            all_symbols_clean = clean_dataframe_for_display(all_symbol_pnl_df)
            st.dataframe(all_symbols_clean,use_container_width=True, height=500, hide_index=True)

    # Charts
    st.markdown('<h3 class="section-header">📈 Performance Charts</h3>', unsafe_allow_html=True)
    fig1, fig2, fig3, fig4, fig5 = create_plotly_charts(performance_by_asset_class, monthly_attrib_usd, asset_classes, perf_df, selected_datetime)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([ "YTD Returns", "ITD Returns", "Market Value", "Monthly PnL", "Yearly PnL"])
    with tab1:
        st.plotly_chart(fig2, use_container_width=True)
    with tab2:
        st.plotly_chart(fig3, use_container_width=True)
    with tab3:
        st.plotly_chart(fig1, use_container_width=True)
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
    st.dataframe(monthly_attrib_usd_formatted,use_container_width=True, height=500)

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
        st.dataframe(pnl_display_df,use_container_width=True, height=600, hide_index=True)

    # Top 10 Symbols Feature
    st.markdown('<h3 class="section-header">🎯 View Top 10 Symbols by Period and Category</h3>', unsafe_allow_html=True)
    st.markdown('**Select a period and category to fetch the top 10 symbols by PnL:**')
    
    # Create columns for better alignment
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        period_select = st.selectbox(
            "Select Period Type",
            options=['Month', 'Year'],
            key='period_select'
        )

    # Show month/year selectors based on period type
    if period_select == 'Month':
        with col2:
            month_select = st.selectbox(
                "Select Month",
                options=range(1, 13),
                format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                key='month_select'
            )
        with col3:
            year_select = st.selectbox(
                "Select Year",
                options=sorted([int(y) for y in pnl_df['Year'].unique()], reverse=True),
                key='year_select'
            )
        with col4:
            category_select = st.selectbox(
                "Select Category",
                options=['Total'] + asset_classes,
                key='category_select'
            )
    else:
        with col2:
            year_select = st.selectbox(
                "Select Year",
                options=sorted([int(y) for y in pnl_df['Year'].unique()], reverse=True),
                key='year_select_fy'
            )
            month_select = None
        with col3:
            category_select = st.selectbox(
                "Select Category",
                options=['Total'] + asset_classes,
                key='category_select'
            )
        with col4:
            st.write("")  # Empty space for alignment

    # Button in a separate row for better visibility
    if st.button("📊 Fetch Top 10 Symbols", use_container_width=False, type="primary"):        
        if period_select == 'Month':
            period_type = 'month'
            period_value = month_select
            year_param = year_select
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            period_display = f"{month_names[month_select-1]} {str(year_select)[-2:]}"
        else:
            period_type = 'year'
            period_value = year_select
            year_param = None
            period_display = f"FY{year_select}"
        
        category = category_select if category_select != 'Total' else None
        category_display = category_select if category_select == 'Total' else category
        
        top_symbols = get_top_symbols_for_period(
            period_type,
            period_value,
            category=category,
            year=year_param,
            top_n=10
        )
        
        if not top_symbols.empty:
            display_top_symbols_modal(top_symbols, period_display, category_display)
        else:
            st.warning(f"No symbols found for {category_display} in {period_display}")

    # Executed Trades Section
    st.markdown(f'<h3 class="section-header">💼 Executed Trades on {selected_date}</h3>', unsafe_allow_html=True)
    if not trades_df.empty:
        trades_clean = clean_dataframe_for_display(trades_df)
        st.dataframe(trades_clean,use_container_width=True, height=500, hide_index=True)
    else:
        st.info(f"No trade data available for {selected_date}")

    # Footer
    st.markdown("---")
    tz = pytz.timezone("Asia/Singapore")
    st.markdown(f"*Dashboard last updated: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()