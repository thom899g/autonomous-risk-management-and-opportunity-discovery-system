"""
Configuration management for the trading system
Centralizes all configurable parameters with validation
"""
import os
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class RiskParameters:
    """Risk management configuration"""
    max_position_size: float = 0.15  # Max 15% in single asset
    max_portfolio_var: float = 0.02  # Max 2% daily VaR
    stop_loss_pct: float = 0.05      # 5% stop loss
    target_sharpe: float = 1.5       # Minimum Sharpe ratio
    correlation_threshold: float = 0.7  # Maximum allowed correlation

@dataclass
class APIConfig:
    """API configuration with rate limiting"""
    polygon_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    firebase_credentials_path: Optional[str] = None
    request_timeout: int = 30
    max_retries: