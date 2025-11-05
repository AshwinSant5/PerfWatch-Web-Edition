"""
Logger - Handles CSV export of collected metrics
"""
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsLogger:
    """Logs metrics to CSV file for export"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.csv_filename: Optional[str] = None
        
    def add_metric(self, metric: Dict[str, Any]):
        """Add a metric entry to the history"""
        if metric is not None:
            self.metrics_history.append(metric)
    
    def start_session(self):
        """Initialize a new logging session"""
        self.metrics_history = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"metrics_{timestamp}.csv"
    
    def export_csv(self, output_dir: str = "logs") -> str:
        """
        Export metrics to CSV file
        
        Args:
            output_dir: Directory to save the CSV file
            
        Returns:
            Path to the exported CSV file
        """
        if not self.metrics_history:
            raise ValueError("No metrics to export")
        
        # Create logs directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not set
        if not self.csv_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_filename = f"metrics_{timestamp}.csv"
        
        filepath = os.path.join(output_dir, self.csv_filename)
        
        # Get all unique keys from metrics
        if not self.metrics_history:
            return filepath
        
        fieldnames = list(self.metrics_history[0].keys())
        
        # Write CSV file
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.metrics_history)
            
            logger.info(f"Exported {len(self.metrics_history)} metrics to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise
    
    def export_json(self, output_dir: str = "logs") -> str:
        """
        Export metrics to JSON file
        
        Args:
            output_dir: Directory to save the JSON file
            
        Returns:
            Path to the exported JSON file
        """
        import json
        
        if not self.metrics_history:
            raise ValueError("No metrics to export")
        
        # Create logs directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not set
        if not self.csv_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"metrics_{timestamp}.json"
        else:
            json_filename = self.csv_filename.replace('.csv', '.json')
        
        filepath = os.path.join(output_dir, json_filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.metrics_history, jsonfile, indent=2)
            
            logger.info(f"Exported {len(self.metrics_history)} metrics to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            raise
    
    def clear_history(self):
        """Clear the metrics history"""
        self.metrics_history = []
        self.csv_filename = None
    
    def get_history_count(self) -> int:
        """Get the number of logged metrics"""
        return len(self.metrics_history)

