import pandas as pd
import numpy as np
import os
from typing import Tuple


class GHDCM:
    """Golden Horse Directional Coefficient Matrix calculator with absolute return weighting."""
    
    def __init__(self, threshold_factor: float = 0.5):
        self.threshold_factor = threshold_factor
        self.df_merged = None
        self.correlation_matrix = None
        self.covariance_matrix = None
    
    def load_data(self, portfolio_df: pd.DataFrame, ghfm_reporting_dir: str) -> pd.DataFrame:
        """
        Load and merge all data sources.
        
        Args:
            portfolio_df: DataFrame with columns ['DATE', 'Daily Return']
            ghfm_reporting_dir: Path to GHFM reporting directory
            
        Returns:
            Merged DataFrame with all returns
        """        
        # Path to index data file
        index_file = os.path.join(ghfm_reporting_dir, "1. Reporting_Data", "Index_Daily_Close_Price.xlsx")
        
        # Load NIFTY data
        nifty_df = pd.read_excel(index_file, sheet_name='Nifty50')
        nifty_df["Date"] = pd.to_datetime(nifty_df["Date"])
        nifty_df = nifty_df.sort_values("Date")
        nifty_df["nifty_return"] = nifty_df["Close"].pct_change()
        nifty_ret = nifty_df[["Date", "nifty_return"]]
        
        # Load S&P 500 data
        snp_df = pd.read_excel(index_file, sheet_name='SnP500')
        snp_df["Date"] = pd.to_datetime(snp_df["Date"])
        snp_df = snp_df.sort_values("Date")
        snp_df["snp_return"] = snp_df["Close"].pct_change()
        snp_ret = snp_df[["Date", "snp_return"]]
        
        # Load MSCI World data
        msci_df = pd.read_excel(index_file, sheet_name='MSCIWorld')
        msci_df["Date"] = pd.to_datetime(msci_df["Date"])
        msci_df = msci_df.sort_values("Date")
        msci_df["msci_return"] = msci_df["Close"].pct_change()
        msci_ret = msci_df[["Date", "msci_return"]]
        
        # Load LEGATRUU data
        legatruu_df = pd.read_excel(index_file, sheet_name='LEGATRUU')
        legatruu_df["Date"] = pd.to_datetime(legatruu_df["Date"])
        legatruu_df = legatruu_df.sort_values("Date")
        legatruu_df["legatruu_return"] = legatruu_df["Close"].pct_change()
        legatruu_ret = legatruu_df[["Date", "legatruu_return"]]
        
        # Process Portfolio data
        portfolio_df = portfolio_df.copy()
        portfolio_df["Date"] = pd.to_datetime(portfolio_df["DATE"])
        portfolio_df = portfolio_df.sort_values("Date")
        portfolio_df["portfolio_return"] = portfolio_df["Daily Return"] / 100
        port_ret = portfolio_df[["Date", "portfolio_return"]]
        
        # Merge all data
        self.df_merged = (
            port_ret.merge(snp_ret, on="Date", how="inner")
                .merge(nifty_ret, on="Date", how="inner")
                .merge(msci_ret, on="Date", how="inner")
                .merge(legatruu_ret, on="Date", how="inner")
        )

        self.df_merged = self.df_merged.dropna().reset_index(drop=True)
        
        return self.df_merged
    
    def _binary_transform(self, series: pd.Series) -> Tuple[np.ndarray, float]:
        """Convert return series into U-series (+1, -1, 0) based on threshold."""
        sigma = series.std()
        H = self.threshold_factor * sigma
        U = np.where(series >= H, 1, np.where(series <= -H, -1, 0))
        return U, sigma
    
    def _absolute_return_weights(self, returns_i: np.ndarray, returns_j: np.ndarray) -> np.ndarray:
        """Calculate weights based on absolute returns for a pair of assets."""
        abs_i = np.abs(returns_i)
        abs_j = np.abs(returns_j)
        
        # Normalize individually
        weights_i = abs_i / abs_i.sum() if abs_i.sum() > 0 else np.ones(len(abs_i)) / len(abs_i)
        weights_j = abs_j / abs_j.sum() if abs_j.sum() > 0 else np.ones(len(abs_j)) / len(abs_j)
        
        # Geometric mean
        weights = np.sqrt(weights_i * weights_j)
        return weights / weights.sum()
    
    def _calculate_gerber(self, Ui: np.ndarray, Uj: np.ndarray, weights: np.ndarray) -> float:
        """Calculate weighted Gerber statistic between two binary series."""
        agreement = ((Ui == 1) & (Uj == 1)) | ((Ui == -1) & (Uj == -1))
        disagreement = ((Ui == 1) & (Uj == -1)) | ((Ui == -1) & (Uj == 1))
        
        weighted_agreement = np.sum(weights * agreement)
        weighted_disagreement = np.sum(weights * disagreement)
        
        total = weighted_agreement + weighted_disagreement
        
        return (weighted_agreement - weighted_disagreement) / total if total > 0 else 0.0
    
    def compute(self, window: int = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Compute GHDCM correlation and covariance matrices using absolute return weighting."""
        if self.df_merged is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Get windowed data
        if window is not None:
            df_windowed = self.df_merged.tail(window).reset_index(drop=True)
        else:
            df_windowed = self.df_merged.copy()
        
        df_returns = df_windowed.drop(columns=['Date'])
        assets = df_returns.columns
        N = len(assets)
                
        # Binary transformation for all assets
        U_dict = {}
        sigma_dict = {}
        for asset in assets:
            U_dict[asset], sigma_dict[asset] = self._binary_transform(df_returns[asset])
        
        # Initialize correlation matrix
        G = pd.DataFrame(np.eye(N), index=assets, columns=assets)
        
        # Calculate pairwise Gerber statistics
        for i, ai in enumerate(assets):
            for j in range(i + 1, N):
                aj = assets[j]
                
                # Calculate weights based on absolute returns
                weights = self._absolute_return_weights(
                    df_returns[ai].values, 
                    df_returns[aj].values
                )
                
                # Calculate Gerber statistic
                gij = self._calculate_gerber(U_dict[ai], U_dict[aj], weights)
                G.loc[ai, aj] = gij
                G.loc[aj, ai] = gij
        
        # Compute covariance matrix
        sigma_vec = np.array([sigma_dict[a] for a in assets])
        D = np.diag(sigma_vec)
        Sigma = pd.DataFrame(D @ G.values @ D, index=assets, columns=assets)
        
        self.correlation_matrix = G
        self.covariance_matrix = Sigma
                
        return G, Sigma, df_windowed["Date"].min(), df_windowed["Date"].max()
