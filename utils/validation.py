"""Input validation helpers."""

from typing import Any, List, Dict, Optional


def validate_price(price: float, min_price: float = 0.0) -> bool:
    """Validate price value."""
    return isinstance(price, (int, float)) and price > min_price


def validate_position_size(size: float, min_size: float = 0.01, max_size: float = 100.0) -> bool:
    """Validate position size."""
    return isinstance(size, (int, float)) and min_size <= size <= max_size


def validate_confidence_score(confidence: float) -> bool:
    """Validate confidence score (0-100%)."""
    return isinstance(confidence, (int, float)) and 0 <= confidence <= 100


def validate_risk_reward_ratio(ratio: float, min_ratio: float = 1.0) -> bool:
    """Validate risk/reward ratio."""
    return isinstance(ratio, (int, float)) and ratio >= min_ratio


def validate_signal_data(signal_data: Dict[str, Any]) -> bool:
    """
    Validate trade signal data completeness.
    
    Args:
        signal_data: Dictionary containing signal data
        
    Returns:
        True if all required fields are valid
    """
    required_fields = [
        "entry_level",
        "stop_loss",
        "take_profit_1",
        "confidence",
    ]
    
    for field in required_fields:
        if field not in signal_data:
            return False
    
    # Validate values
    if not validate_price(signal_data["entry_level"]):
        return False
    if not validate_price(signal_data["stop_loss"]):
        return False
    if not validate_confidence_score(signal_data["confidence"]):
        return False
    
    return True
