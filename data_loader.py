import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List
import json
import warnings
warnings.filterwarnings('ignore')

class IPLDataLoader:
    """Load and preprocess IPL cricket data"""
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = Path(data_dir)
        self.matches_df = None
        self.deliveries_df = None
        self.ground_mapping = self._load_ground_mapping()
    
    def _load_ground_mapping(self) -> Dict[str, str]:
        """Load ground name mapping from JSON file"""
        try:
            mapping_file = self.data_dir / 'ground_names.json'
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    mapping_dict = json.load(f)
                # Create reverse mapping: old_name -> canonical_name
                reverse_mapping = {}
                for canonical_name, aliases in mapping_dict.items():
                    for alias in aliases:
                        reverse_mapping[alias] = canonical_name
                return reverse_mapping
            return {}
        except Exception as e:
            print(f"Warning: Could not load ground mapping: {e}")
            return {}
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load matches and deliveries CSV files"""
        try:
            self.matches_df = pd.read_csv(self.data_dir / 'matches.csv')
            self.deliveries_df = pd.read_csv(self.data_dir / 'deliveries.csv')
            
            # Clean column names
            self.matches_df.columns = self.matches_df.columns.str.strip()
            self.deliveries_df.columns = self.deliveries_df.columns.str.strip()
            
            # Standardize ground names
            if self.ground_mapping:
                self.matches_df['venue'] = self.matches_df['venue'].map(
                    lambda x: self.ground_mapping.get(x, x)
                )
            
            print(f"Loaded {len(self.matches_df)} matches")
            print(f"Loaded {len(self.deliveries_df)} deliveries")
            
            return self.matches_df, self.deliveries_df
        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            return None, None
    
    def preprocess_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Clean and preprocess the data"""
        if self.matches_df is None or self.deliveries_df is None:
            self.load_data()
        
        # Convert date columns
        self.matches_df['date'] = pd.to_datetime(self.matches_df['date'], errors='coerce')
        
        # Handle missing values in key columns
        self.deliveries_df['batsman_runs'] = pd.to_numeric(
            self.deliveries_df.get('batsman_runs', 0), errors='coerce'
        ).fillna(0).astype(int)
        self.deliveries_df['extra_runs'] = pd.to_numeric(
            self.deliveries_df.get('extra_runs', 0), errors='coerce'
        ).fillna(0).astype(int)
        self.deliveries_df['total_runs'] = pd.to_numeric(
            self.deliveries_df.get('total_runs', 0), errors='coerce'
        ).fillna(0).astype(int)
        
        print("Data preprocessing completed")
        return self.matches_df, self.deliveries_df
    
    def get_matches_by_year(self, year: int) -> pd.DataFrame:
        """Get all matches for a specific year"""
        if self.matches_df is None:
            self.load_data()
        return self.matches_df[self.matches_df['year'] == year]
    
    def get_team_matches(self, team: str) -> pd.DataFrame:
        """Get all matches for a specific team"""
        if self.matches_df is None:
            self.load_data()
        return self.matches_df[
            (self.matches_df['team1'] == team) | (self.matches_df['team2'] == team)
        ]
    
    def get_deliveries_for_match(self, match_id: int) -> pd.DataFrame:
        """Get all deliveries for a specific match"""
        if self.deliveries_df is None:
            self.load_data()
        return self.deliveries_df[self.deliveries_df['match_id'] == match_id]
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of the dataset"""
        if self.matches_df is None:
            self.load_data()
        
        return {
            'total_matches': len(self.matches_df),
            'seasons': self.matches_df['season'].nunique(),
            'teams': len(set(list(self.matches_df['team1'].unique()) + list(self.matches_df['team2'].unique()))),
            'venues': self.matches_df['venue'].nunique(),
            'date_range': (self.matches_df['date'].min(), self.matches_df['date'].max())
        }


if __name__ == "__main__":
    loader = IPLDataLoader()
    matches, deliveries = loader.load_data()
    matches, deliveries = loader.preprocess_data()
    print(loader.get_summary_stats())
