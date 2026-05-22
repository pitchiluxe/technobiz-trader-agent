"""
TradingView Data Provider - Alternative to MetaTrader 5

Provides market data from TradingView API for multi-market analysis.
Uses tradingview-ta package for technical analysis and indicators.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

try:
    from tradingview_ta import AnalysisIndicators
    TRADINGVIEW_AVAILABLE = True
except ImportError:
    TRADINGVIEW_AVAILABLE = False
    print("Warning: tradingview-ta not installed. Install with: pip install tradingview-ta")

logger = logging.getLogger(__name__)


@dataclass
class Candle:
    """Standard candle data structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class OHLCData:
    """OHLC data structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


class TradingViewProvider:
    """
    Data provider using TradingView technical analysis API.
    
    Features:
    - Free technical analysis for all markets
    - Support for multiple timeframes
    - Technical indicators (RSI, MACD, etc.)
    - Multi-market support (forex, crypto, stocks, commodities)
    
    Limitations:
    - Free tier has 1-minute delayed data
    - Limited to TradingView API capabilities
    - No direct execution (use MT5 for that)
    """
    
    def __init__(self):
        """Initialize TradingView provider"""
        if not TRADINGVIEW_AVAILABLE:
            raise ImportError(
                "tradingview-ta package not installed. "
                "Install with: pip install tradingview-ta"
            )
        
        self.name = "TradingView"
        self.api_type = "free"  # or "premium"
        logger.info("TradingView provider initialized")
    
    def get_analysis(
        self, 
        symbol: str, 
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get technical analysis for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD", "OANDA:EURUSD", "BINANCE:BTCUSD")
            interval: Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo)
        
        Returns:
            Dictionary with analysis results including:
            - recommendation: "BUY", "SELL", or "NEUTRAL"
            - buy_signals: Number of buy signals
            - sell_signals: Number of sell signals
            - indicators: Dictionary of indicator values
        """
        try:
            # Normalize symbol format
            symbol = self._normalize_symbol(symbol)
            
            # Get analysis from TradingView
            analysis = AnalysisIndicators(symbol=symbol, interval=interval)
            
            # Extract recommendation
            summary = analysis.summary
            
            # Build response
            result = {
                "symbol": symbol,
                "interval": interval,
                "timestamp": datetime.now(),
                "recommendation": summary.get("RECOMMENDATION", "NEUTRAL"),
                "buy_signals": summary.get("BUY", 0),
                "sell_signals": summary.get("SELL", 0),
                "neutral_signals": summary.get("NEUTRAL", 0),
                "indicators": self._extract_indicators(analysis),
            }
            
            logger.debug(f"Analysis for {symbol} ({interval}): {result['recommendation']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting analysis for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "interval": interval,
                "recommendation": "NEUTRAL",
                "error": str(e),
            }
    
    def get_multi_timeframe_analysis(
        self, 
        symbol: str,
        intervals: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get analysis for multiple timeframes.
        
        Args:
            symbol: Trading symbol
            intervals: List of timeframes (default: ["1d", "4h", "1h"])
        
        Returns:
            Dictionary with analysis for each timeframe
        """
        if intervals is None:
            intervals = ["1d", "4h", "1h"]
        
        results = {}
        for interval in intervals:
            results[interval] = self.get_analysis(symbol, interval)
        
        return results
    
    def get_consensus(
        self, 
        symbol: str,
        intervals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get consensus recommendation across multiple timeframes.
        
        Args:
            symbol: Trading symbol
            intervals: List of timeframes
        
        Returns:
            Consensus recommendation and confidence
        """
        if intervals is None:
            intervals = ["1d", "4h", "1h"]
        
        analyses = self.get_multi_timeframe_analysis(symbol, intervals)
        
        # Count signals
        buy_count = 0
        sell_count = 0
        neutral_count = 0
        
        for analysis in analyses.values():
            recommendation = analysis.get("recommendation", "NEUTRAL")
            if recommendation == "BUY":
                buy_count += 1
            elif recommendation == "SELL":
                sell_count += 1
            else:
                neutral_count += 1
        
        # Determine consensus
        total = len(intervals)
        confidence = max(buy_count, sell_count, neutral_count) / total * 100
        
        if buy_count > sell_count and buy_count > neutral_count:
            consensus = "BUY"
        elif sell_count > buy_count and sell_count > neutral_count:
            consensus = "SELL"
        else:
            consensus = "NEUTRAL"
        
        return {
            "symbol": symbol,
            "consensus": consensus,
            "confidence": confidence,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "neutral_count": neutral_count,
            "analyses": analyses,
        }
    
    def scan_symbols(
        self, 
        symbols: List[str],
        interval: str = "1d"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Scan multiple symbols for signals.
        
        Args:
            symbols: List of trading symbols
            interval: Timeframe to analyze
        
        Returns:
            Dictionary with analysis for each symbol
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_analysis(symbol, interval)
        
        return results
    
    def get_screener_results(
        self,
        market: str = "forex",
        interval: str = "1d"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get screener results for a market.
        
        Args:
            market: Market to screen (forex, crypto, stocks, etc.)
            interval: Timeframe to analyze
        
        Returns:
            Dictionary with top signals
        """
        # Define popular symbols by market
        markets = {
            "forex": ["EURUSD", "GBPUSD", "USDJPY", "EURGBP", "GBPJPY"],
            "crypto": ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD"],
            "commodities": ["XAUUSD", "WTIUSD", "NGAS"],
        }
        
        symbols = markets.get(market, [])
        if not symbols:
            logger.warning(f"Unknown market: {market}")
            return {}
        
        return self.scan_symbols(symbols, interval)
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to TradingView format.
        
        Examples:
        - "EURUSD" → "OANDA:EURUSD" or "FOREX:EURUSD"
        - "BTCUSD" → "BINANCE:BTCUSD"
        - "AAPL" → "NASDAQ:AAPL"
        """
        # If already has exchange prefix, use as-is
        if ":" in symbol:
            return symbol
        
        # Auto-prefix based on symbol patterns
        symbol = symbol.upper()
        
        # Detect market type and add prefix
        if symbol.endswith("USD") and len(symbol) in [6, 7]:
            # Likely forex (EURUSD, GBPUSD) or crypto (BTCUSD)
            if symbol in ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD"]:
                return f"OANDA:{symbol}"
            elif symbol in ["XAUUSD", "XAGUSD", "WTIUSD", "NGAS"]:
                return f"OANDA:{symbol}"
            else:
                # Assume crypto
                return f"BINANCE:{symbol}"
        elif len(symbol) <= 5:
            # Likely stock
            return f"NASDAQ:{symbol}"
        else:
            # Return as-is, let API handle it
            return symbol
    
    def _extract_indicators(self, analysis: Any) -> Dict[str, float]:
        """
        Extract key technical indicators from analysis.
        
        Returns dictionary with common indicators.
        """
        indicators = {}
        
        # Key indicators to extract
        indicator_names = [
            "RSI", "STOCH.K", "STOCH.D", "MACD", "ADX", "CCI",
            "ATR", "BBPERCENT", "EMA200", "SMA200", "SAR"
        ]
        
        for indicator in indicator_names:
            try:
                value = analysis.get(indicator)
                if value is not None:
                    indicators[indicator] = float(value)
            except (ValueError, TypeError):
                pass
        
        return indicators
    
    def get_support_resistance(
        self, 
        symbol: str,
        interval: str = "1d"
    ) -> Dict[str, List[float]]:
        """
        Get approximate support and resistance levels based on Bollinger Bands.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe
        
        Returns:
            Dictionary with support and resistance levels
        """
        analysis = self.get_analysis(symbol, interval)
        indicators = analysis.get("indicators", {})
        
        # Extract from indicators if available
        result = {
            "resistance": [],
            "support": [],
            "middle": None,
        }
        
        # Note: Actual S/R calculation would require price data
        # This is simplified version using Bollinger Bands if available
        
        return result
    
    def test_connection(self) -> bool:
        """
        Test if TradingView API is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get analysis for a common symbol
            analysis = AnalysisIndicators(symbol="OANDA:EURUSD", interval="1d")
            recommendation = analysis.summary.get("RECOMMENDATION")
            
            if recommendation in ["BUY", "SELL", "NEUTRAL"]:
                logger.info("TradingView connection test: SUCCESS")
                return True
            else:
                logger.warning("TradingView connection test: UNEXPECTED RESPONSE")
                return False
                
        except Exception as e:
            logger.error(f"TradingView connection test failed: {str(e)}")
            return False


class HybridDataProvider:
    """
    Hybrid provider that uses both TradingView (analysis) and MT5 (execution).
    
    Workflow:
    1. Get technical analysis from TradingView
    2. Get real-time prices from MT5
    3. Combine for best-of-both analysis
    """
    
    def __init__(self, use_tradingview: bool = True, use_mt5: bool = True):
        """
        Initialize hybrid provider.
        
        Args:
            use_tradingview: Enable TradingView for analysis
            use_mt5: Enable MT5 for prices/execution
        """
        self.tradingview = None
        self.mt5 = None
        
        if use_tradingview:
            try:
                self.tradingview = TradingViewProvider()
                logger.info("Hybrid provider: TradingView enabled")
            except Exception as e:
                logger.warning(f"Could not initialize TradingView: {str(e)}")
        
        if use_mt5:
            try:
                from market_data.mt5_provider import MT5Provider
                self.mt5 = MT5Provider()
                logger.info("Hybrid provider: MT5 enabled")
            except Exception as e:
                logger.warning(f"Could not initialize MT5: {str(e)}")
    
    def get_hybrid_analysis(
        self, 
        symbol: str,
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get combined analysis from TradingView + MT5.
        """
        result = {
            "symbol": symbol,
            "interval": interval,
            "timestamp": datetime.now(),
        }
        
        # Get TradingView analysis
        if self.tradingview:
            tv_analysis = self.tradingview.get_analysis(symbol, interval)
            result["tradingview"] = tv_analysis
            result["recommendation"] = tv_analysis.get("recommendation", "NEUTRAL")
        
        # Get MT5 data if available
        if self.mt5:
            try:
                price = self.mt5.get_current_price(symbol)
                if price:
                    result["current_price"] = price
            except:
                pass
        
        return result
