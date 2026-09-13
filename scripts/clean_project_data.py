"""
Data cleaning and preprocessing module for Mwense Town Council project data.

This module provides reusable functions for:
1. Loading extracted raw CSV data
2. Cleaning project names and fields
3. Standardizing values (sector, funding, status)
4. Removing duplicates
5. Adding missing metadata
6. Validating data quality
7. Exporting to final format

Usage in notebook:
    from scripts.clean_project_data import ProjectCleaner
    
    cleaner = ProjectCleaner("clean_data/raw_projects_2025_unclean.csv")
    clean_df = cleaner.run()
    clean_df.to_csv("outputs/projects_clean.csv", sep="|", index=False)
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings("ignore")


class ProjectCleaner:
    """Clean and preprocess Mwense council project data."""
    
    # Standardization mappings
    SECTOR_RULES = {
        "Education": ["school", "classroom", "crb", "bursary", "primary", "secondary"],
        "Health": ["hospital", "health", "mortuary", "clinic", "medical"],
        "Water": ["water", "borehole", "piped", "sanitation", "drainage", "tank"],
        "Infrastructure": ["road", "bridge", "crossing", "skip", "truck", "fire", "bus", "station", "chalets"],
        "Energy": ["electricity", "electrification", "transformer", "street light", "power"],
        "Security": ["police", "cell", "security", "holding"],
        "Administration": ["council", "office", "furniture", "equipment"],
    }
    
    FUNDING_STANDARDIZE = {
        "basic capital grant": "Basic Capital Grant",
        "motor licensing fund": "Motor Licensing Fund",
        "locally generated revenue": "Own-Source Revenue",
        "own source revenue": "Own-Source Revenue",
        "cdf": "Constituency Development Fund",
        "constituency development fund": "Constituency Development Fund",
    }
    
    def __init__(self, csv_path: str):
        """Initialize cleaner with raw CSV file."""
        self.csv_path = Path(csv_path)
        self.df_raw = None
        self.df_clean = None
        self.cleaning_report = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load raw CSV data."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"File not found: {self.csv_path}")
        
        self.df_raw = pd.read_csv(self.csv_path, sep="|", dtype=str)
        print(f"✓ Loaded {len(self.df_raw)} records from {self.csv_path.name}")
        return self.df_raw
    
    def clean_project_names(self) -> pd.DataFrame:
        """Clean and normalize project names."""
        self.df_clean = self.df_raw.copy()
        
        # Remove leading numbers and extra whitespace
        self.df_clean['project_name'] = self.df_clean['project_name'].fillna("")
        self.df_clean['project_name'] = self.df_clean['project_name'].str.replace(r"^\d+\s*[-.]?\s*", "", regex=True)
        self.df_clean['project_name'] = self.df_clean['project_name'].str.strip()
        self.df_clean['project_name'] = self.df_clean['project_name'].str.title()
        
        # Replace empty with "Not specified"
        self.df_clean.loc[self.df_clean['project_name'].str.len() < 3, 'project_name'] = "Not Specified"
        
        empty_before = self.df_raw['project_name'].fillna("").str.len().eq(0).sum()
        empty_after = self.df_clean['project_name'].eq("Not Specified").sum()
        
        self.cleaning_report['project_name_cleaned'] = empty_before
        print(f"  ✓ Cleaned project names ({empty_before} standardized)")
        
        return self.df_clean
    
    def standardize_funding_sources(self) -> pd.DataFrame:
        """Standardize funding source field."""
        self.df_clean['funding_source'] = self.df_clean['funding_source'].fillna("Not specified")
        self.df_clean['funding_source'] = self.df_clean['funding_source'].str.strip()
        self.df_clean['funding_source'] = self.df_clean['funding_source'].str.lower()
        
        # Map to standard values
        self.df_clean['funding_source'] = self.df_clean['funding_source'].map(
            lambda x: self.FUNDING_STANDARDIZE.get(x, x.title())
        )
        
        self.cleaning_report['funding_standardized'] = True
        print(f"  ✓ Standardized funding sources: {self.df_clean['funding_source'].unique().tolist()}")
        
        return self.df_clean
    
    def improve_sector_classification(self) -> pd.DataFrame:
        """Improve sector classification based on project name."""
        def classify_sector(text):
            text_lower = str(text).lower()
            for sector, keywords in self.SECTOR_RULES.items():
                if any(keyword in text_lower for keyword in keywords):
                    return sector
            return "Other"
        
        self.df_clean['sector'] = self.df_clean['project_name'].apply(classify_sector)
        
        self.cleaning_report['sector_distribution'] = self.df_clean['sector'].value_counts().to_dict()
        print(f"  ✓ Sector classification: {self.cleaning_report['sector_distribution']}")
        
        return self.df_clean
    
    def standardize_wards(self) -> pd.DataFrame:
        """Standardize ward information."""
        # Capital projects are district-wide
        self.df_clean.loc[self.df_clean['project_type'] == 'Capital Project', 'ward'] = "District-wide"
        
        # CDF projects should have specific wards
        self.df_clean.loc[self.df_clean['project_type'] == 'CDF Project', 'ward'] = \
            self.df_clean.loc[self.df_clean['project_type'] == 'CDF Project', 'ward'].str.title()
        
        # Replace "Not specified" with null for further processing
        self.df_clean['ward'] = self.df_clean['ward'].replace("Not Specified", "District-wide")
        
        self.cleaning_report['wards_standardized'] = True
        print(f"  ✓ Ward information standardized")
        
        return self.df_clean
    
    def remove_duplicates(self) -> pd.DataFrame:
        """Identify and remove duplicate records."""
        duplicates = self.df_clean[
            self.df_clean.duplicated(subset=['project_name', 'sector'], keep=False)
        ]
        
        if len(duplicates) > 0:
            print(f"  ⚠ Found {len(duplicates) // 2} duplicate records:")
            print(f"     {duplicates['project_name'].value_counts()}")
            
            # Keep first occurrence
            self.df_clean = self.df_clean.drop_duplicates(
                subset=['project_name', 'sector'],
                keep='first'
            )
            
            self.cleaning_report['duplicates_removed'] = len(duplicates) // 2
        else:
            self.cleaning_report['duplicates_removed'] = 0
        
        print(f"  ✓ After deduplication: {len(self.df_clean)} records")
        return self.df_clean
    
    def add_missing_fields(self, access_date: str = "2026-09-13") -> pd.DataFrame:
        """Add missing metadata fields."""
        # Add missing columns
        new_fields = {
            'budget_amount_zmw': None,
            'project_status': 'Approved',
            'start_date': None,
            'completion_date': None,
            'beneficiaries': '',
            'extraction_notes': 'Extracted from approved projects list',
            'access_date': access_date,
        }
        
        for field, default_value in new_fields.items():
            if field not in self.df_clean.columns:
                self.df_clean[field] = default_value
        
        self.cleaning_report['fields_added'] = len(new_fields)
        print(f"  ✓ Added {len(new_fields)} metadata fields")
        
        return self.df_clean
    
    def regenerate_record_ids(self, prefix: str = "PRJ") -> pd.DataFrame:
        """Generate consistent record IDs."""
        self.df_clean['record_id'] = [
            f"{prefix}_{str(i).zfill(4)}" for i in range(1, len(self.df_clean) + 1)
        ]
        
        print(f"  ✓ Regenerated record IDs ({prefix}_0001 format)")
        return self.df_clean
    
    def validate_data(self) -> bool:
        """Run validation checks."""
        print("\n  VALIDATION CHECKS:")
        
        checks = {
            "Unique record IDs": self.df_clean['record_id'].is_unique,
            "No null project names": self.df_clean['project_name'].notna().all(),
            "Valid sectors": self.df_clean['sector'].isin(
                list(self.SECTOR_RULES.keys()) + ["Other"]
            ).all(),
            "Valid project types": self.df_clean['project_type'].isin(
                ["Capital Project", "CDF Project"]
            ).all(),
            "Year values are valid": self.df_clean['year'].astype(int).between(2020, 2030).all(),
        }
        
        all_passed = True
        for check_name, result in checks.items():
            status = "✓" if result else "✗"
            print(f"    {status} {check_name}: {result}")
            if not result:
                all_passed = False
        
        self.cleaning_report['validation_passed'] = all_passed
        return all_passed
    
    def print_summary(self):
        """Print cleaning summary."""
        print("\n" + "=" * 70)
        print("DATA CLEANING SUMMARY")
        print("=" * 70)
        print(f"Records processed: {len(self.df_raw)} → {len(self.df_clean)}")
        print(f"Duplicates removed: {self.cleaning_report.get('duplicates_removed', 0)}")
        print(f"Sector distribution: {self.cleaning_report.get('sector_distribution', {})}")
        print(f"Validation: {'PASSED ✓' if self.cleaning_report.get('validation_passed') else 'FAILED ✗'}")
        print("=" * 70 + "\n")
    
    def run(self, access_date: str = "2026-09-13") -> pd.DataFrame:
        """Execute complete cleaning pipeline."""
        print("\n" + "=" * 70)
        print("CLEANING EXTRACTED PROJECT DATA")
        print("=" * 70 + "\n")
        
        self.load_data()
        self.clean_project_names()
        self.standardize_funding_sources()
        self.improve_sector_classification()
        self.standardize_wards()
        self.remove_duplicates()
        self.add_missing_fields(access_date)
        self.regenerate_record_ids()
        self.validate_data()
        self.print_summary()
        
        return self.df_clean
    
    def get_quality_metrics(self) -> Dict:
        """Get data quality metrics."""
        if self.df_clean is None:
            return {}
        
        return {
            "total_records": len(self.df_clean),
            "unique_sectors": self.df_clean['sector'].nunique(),
            "unique_wards": self.df_clean['ward'].nunique(),
            "missing_budget_info": self.df_clean['budget_amount_zmw'].isna().sum(),
            "missing_dates": self.df_clean['start_date'].isna().sum(),
            "data_completeness_pct": round(
                (1 - self.df_clean.isnull().sum().sum() / (len(self.df_clean) * len(self.df_clean.columns))) * 100,
                2
            ),
            "sector_breakdown": self.df_clean['sector'].value_counts().to_dict(),
            "funding_breakdown": self.df_clean['funding_source'].value_counts().to_dict(),
        }


if __name__ == "__main__":
    # Example usage
    cleaner = ProjectCleaner("clean_data/raw_projects_2025_unclean.csv")
    clean_df = cleaner.run()
    
    # Display metrics
    metrics = cleaner.get_quality_metrics()
    print("QUALITY METRICS:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Save
    output_file = Path("clean_data/projects_2025_clean.csv")
    clean_df.to_csv(output_file, sep="|", index=False)
    print(f"\n✓ Saved {len(clean_df)} clean records to {output_file.name}")
