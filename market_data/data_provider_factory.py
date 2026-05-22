"""
Data Provider Factory - Creates appropriate data provider based on configuration.

Supports:
- MT5 (MetaTrader 5) - Real-time trading execution
- TradingView - Advanced technical analysis
- Hybrid - Both TradingView + MT5 combined
"""

import logging
from typing import Union, Optional
from market_data.mt5_provider import MT5Provider
from market_data.tradingview_provider import TradingViewProvider, HybridDataProvider
from config.settings import settings

logger = logging.getLogger(__name__)


def create_data_provider() -> Union[MT5Provider, TradingViewProvider, HybridDataProvider]:
    """
    Factory function to create the appropriate data provider.
    
    Returns:
        Data provider instance based on DATA_PROVIDER setting
    
    Raises:
        ValueError: If configuration is invalid or provider cannot be initialized
    """
    provider_type = settings.DATA_PROVIDER.lower()
    
    logger.info(f"Creating data provider: {provider_type}")
    
    if provider_type == "mt5":
        logger.info("Using MetaTrader 5 provider for market data and execution")
        return MT5Provider()
    
    elif provider_type == "tradingview":
        logger.info("Using TradingView provider for technical analysis")
        return TradingViewProvider()
    
    elif provider_type == "hybrid":
        logger.info("Using Hybrid provider (TradingView analysis + MT5 execution)")
        return HybridDataProvider(use_tradingview=True, use_mt5=True)
    
    else:
        raise ValueError(
            f"Unknown DATA_PROVIDER: {provider_type}. "
            "Must be 'mt5', 'tradingview', or 'hybrid'."
        )


def get_data_provider_info() -> dict:
    """
    Get information about the current data provider configuration.
    
    Returns:
        Dictionary with provider details
    """
    provider_type = settings.DATA_PROVIDER.lower()
    
    info = {
        "provider": provider_type,
        "api_type": "N/A",
        "execution_capable": False,
        "analysis_capable": False,
    }
    
    if provider_type == "mt5":
        info.update({
            "api_type": "MetaTrader 5 Python SDK",
            "execution_capable": True,
            "analysis_capable": True,
            "account": settings.MT5_ACCOUNT[:4] + "****" if settings.MT5_ACCOUNT else "Not configured",
        })
    
    elif provider_type == "tradingview":
        info.update({
            "api_type": settings.TRADINGVIEW_API_TYPE,
            "execution_capable": False,
            "analysis_capable": True,
            "exchange": settings.TRADINGVIEW_EXCHANGE,
            "note": "Execution requires external broker integration",
        })
    
    elif provider_type == "hybrid":
        info.update({
            "api_type": f"TradingView ({settings.TRADINGVIEW_API_TYPE}) + MT5",
            "execution_capable": True,
            "analysis_capable": True,
            "tradingview_exchange": settings.TRADINGVIEW_EXCHANGE,
            "mt5_account": settings.MT5_ACCOUNT[:4] + "****" if settings.MT5_ACCOUNT else "Not configured",
        })
    
    return info


def validate_data_provider() -> bool:
    """
    Validate that the data provider can be initialized and is accessible.
    
    Returns:
        True if validation passed, False otherwise
    """
    try:
        provider = create_data_provider()
        
        # Test connection based on provider type
        if isinstance(provider, MT5Provider):
            logger.info("Validating MT5 connection...")
            is_valid = provider.is_connected()
        
        elif isinstance(provider, TradingViewProvider):
            logger.info("Validating TradingView connection...")
            is_valid = provider.test_connection()
        
        elif isinstance(provider, HybridDataProvider):
            logger.info("Validating Hybrid provider...")
            # Test both components
            tv_valid = True
            mt5_valid = True
            
            if provider.tradingview:
                tv_valid = provider.tradingview.test_connection()
            
            if provider.mt5:
                mt5_valid = provider.mt5.is_connected()
            
            is_valid = tv_valid or mt5_valid
        
        else:
            is_valid = False
        
        if is_valid:
            logger.info(f"✅ Data provider validation: PASS")
        else:
            logger.warning(f"⚠️  Data provider validation: FAILED")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"Data provider validation failed: {str(e)}")
        return False


if __name__ == "__main__":
    """Test the data provider factory"""
    
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Get provider info
    info = get_data_provider_info()
    print("\nData Provider Configuration:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Validate provider
    print("\nValidating data provider...")
    is_valid = validate_data_provider()
    
    if is_valid:
        # Try to create provider
        print("\nCreating data provider...")
        provider = create_data_provider()
        print(f"✅ Provider created successfully: {type(provider).__name__}")
    else:
        print("❌ Provider validation failed")
