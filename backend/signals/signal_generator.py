import numpy as np
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Generate trading signals based on market analysis"""
    
    def __init__(self):
        self.signals_history = {}
    
    def calculate_sma(self, df, period):
        """Calculate Simple Moving Average"""
        return df['close'].rolling(window=period).mean()
    
    def calculate_rsi(self, df, period=14):
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def generate_signal(self, symbol, df):
        """
        Generate trading signal based on multiple indicators
        
        Returns:
            Dictionary with signal data
        """
        try:
            if df is None or len(df) < 26:
                return {
                    'symbol': symbol,
                    'signal': 'HOLD',
                    'score': 0,
                    'price': None,
                    'trend': 'NEUTRAL',
                    'indicators': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            # Calculate indicators
            sma20 = self.calculate_sma(df, 20)
            sma50 = self.calculate_sma(df, 50)
            rsi = self.calculate_rsi(df)
            macd, signal_line, histogram = self.calculate_macd(df)
            upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df)
            
            current_price = df['close'].iloc[-1]
            current_rsi = rsi.iloc[-1]
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            
            # Initialize signal score
            score = 50  # Neutral score
            buy_signals = 0
            sell_signals = 0
            
            # SMA Analysis
            if sma20.iloc[-1] > sma50.iloc[-1]:
                buy_signals += 1
                trend = 'UPTREND'
            else:
                sell_signals += 1
                trend = 'DOWNTREND'
            
            # RSI Analysis
            if current_rsi < 30:
                buy_signals += 2
            elif current_rsi > 70:
                sell_signals += 2
            else:
                buy_signals += 0.5
            
            # MACD Analysis
            if current_macd > current_signal:
                buy_signals += 1
            else:
                sell_signals += 1
            
            # Bollinger Bands Analysis
            if current_price < lower_band.iloc[-1]:
                buy_signals += 1
            elif current_price > upper_band.iloc[-1]:
                sell_signals += 1
            
            # Determine final signal
            if buy_signals > sell_signals + 1:
                signal = 'BUY'
                score = min(100, 50 + (buy_signals * 10))
            elif sell_signals > buy_signals + 1:
                signal = 'SELL'
                score = max(0, 50 - (sell_signals * 10))
            else:
                signal = 'HOLD'
                score = 50
            
            result = {
                'symbol': symbol,
                'signal': signal,
                'score': round(score, 2),
                'price': round(current_price, 5),
                'trend': trend,
                'indicators': {
                    'rsi': round(current_rsi, 2),
                    'macd': round(current_macd, 5),
                    'sma20': round(sma20.iloc[-1], 5),
                    'sma50': round(sma50.iloc[-1], 5),
                    'upper_band': round(upper_band.iloc[-1], 5),
                    'lower_band': round(lower_band.iloc[-1], 5)
                },
                'timestamp': datetime.now().isoformat(),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals
            }
            
            self.signals_history[symbol] = result
            return result
        
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'signal': 'HOLD',
                'score': 0,
                'price': None,
                'trend': 'ERROR',
                'indicators': {},
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }