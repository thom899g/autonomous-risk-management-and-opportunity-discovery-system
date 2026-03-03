#!/usr/bin/env python3
"""
Autonomous Risk Management and Opportunity Discovery System
Core Orchestrator - Manages the complete trading ecosystem
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import Config
from data_ingestor import MarketDataIngestor
from sentiment_analyzer import NewsSentimentAnalyzer
from portfolio_optimizer import RiskAwarePortfolioOptimizer
from firebase_manager import FirebaseStateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutonomousTradingSystem:
    """Main orchestrator for the autonomous trading ecosystem"""
    
    def __init__(self):
        """Initialize all system components with dependency injection"""
        logger.info("Initializing Autonomous Trading System")
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize components
        self.data_ingestor = MarketDataIngestor(self.config)
        self.sentiment_analyzer = NewsSentimentAnalyzer(self.config)
        self.portfolio_optimizer = RiskAwarePortfolioOptimizer(self.config)
        self.state_manager = FirebaseStateManager(self.config)
        
        # System state
        self.is_running = False
        self.current_portfolio = {}
        self.market_regime = "NORMAL"
        
        logger.info("System initialization complete")
    
    async def run_cycle(self) -> Dict:
        """
        Execute one complete analysis cycle
        Returns: Dictionary with all analysis results
        """
        try:
            logger.info("Starting analysis cycle")
            
            # 1. Fetch market data
            market_data = await self.data_ingestor.fetch_market_data()
            
            # 2. Analyze news sentiment
            sentiment_scores = await self.sentiment_analyzer.analyze_news_feed()
            
            # 3. Optimize portfolio with risk constraints
            portfolio_decisions = self.portfolio_optimizer.optimize_portfolio(
                market_data=market_data,
                sentiment_scores=sentiment_scores,
                current_portfolio=self.current_portfolio
            )
            
            # 4. Update state in Firebase
            await self.state_manager.update_system_state({
                'timestamp': datetime.utcnow().isoformat(),
                'market_data': market_data,
                'sentiment': sentiment_scores,
                'portfolio_decisions': portfolio_decisions,
                'market_regime': self.market_regime
            })
            
            # 5. Update internal state
            self.current_portfolio = portfolio_decisions.get('allocations', {})
            
            logger.info(f"Cycle completed. Portfolio decisions: {portfolio_decisions}")
            return portfolio_decisions
            
        except Exception as e:
            logger.error(f"Error in analysis cycle: {str(e)}", exc_info=True)
            # Implement circuit breaker pattern
            if "rate_limit" in str(e).lower():
                await asyncio.sleep(60)  # Backoff for rate limits
            raise
    
    async def run_continuously(self, interval_seconds: int = 300):
        """
        Run the system continuously with specified interval
        Args:
            interval_seconds: Time between cycles (default 5 minutes)
        """
        self.is_running = True
        logger.info(f"Starting continuous operation with {interval_seconds}s intervals")
        
        while self.is_running:
            try:
                start_time = datetime.utcnow()
                
                await self.run_cycle()
                
                # Calculate sleep time to maintain interval
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.1f} seconds")
                    await asyncio.sleep(sleep_time)
                    
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                self.is_running = False
            except Exception as e:
                logger.error(f"Critical system error: {e}")
                # Emergency shutdown on repeated failures
                if "connection" in str(e).lower():
                    logger.critical("Connection failure - initiating shutdown")
                    self.is_running = False
    
    def emergency_shutdown(self):
        """Emergency shutdown procedure"""
        logger.critical("Initiating emergency shutdown")
        self.is_running = False
        # Save final state
        asyncio.run(self.state_manager.save_emergency_state(self.current_portfolio))

async def main():
    """Entry point for the trading system"""
    system = AutonomousTradingSystem()
    
    try:
        # Run for one cycle to test
        # result = await system.run_cycle()
        
        # Or run continuously
        await system.run_continuously(interval_seconds=300)
        
    except Exception as e:
        logger.critical(f"Fatal system error: {e}")
        system.emergency_shutdown()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())