import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MT5Connector:
    """Handle connections and data retrieval from MetaTrader 5"""
    
    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        self.connect()
    
    def connect(self):
        """Establish connection to MT5"""
        try:
            if not mt5.initialize(login=self.login, password=self.password, server=self.server):
                logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
                self.connected = False
                return
            self.connected = True
            logger.info("MT5 connection established")
        except Exception as e:
            logger.error(f"MT5 connection error: {str(e)}")
            self.connected = False
    
    def is_connected(self):
        """Check if MT5 is connected"""
        return self.connected and mt5.terminal_info().connected
    
    def get_price_data(self, symbol, timeframe, count):
        """
        Retrieve price data from MT5
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe constant (e.g., mt5.TIMEFRAME_H1)
            count: Number of bars to retrieve
        
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            if not self.is_connected():
                self.connect()
            
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None:
                logger.warning(f"Failed to get data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
            df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
            
            return df
        except Exception as e:
            logger.error(f"Error retrieving price data for {symbol}: {str(e)}")
            return None
    
    def get_account_info(self):
        """Get account information from MT5"""
        try:
            if not self.is_connected():
                return None
            
            account_info = mt5.account_info()
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'margin_level': account_info.margin_level,
                'margin_free': account_info.margin_free,
                'profit': account_info.profit
            }
        except Exception as e:
            logger.error(f"Error retrieving account info: {str(e)}")
            return None
    
    def disconnect(self):
        """Close MT5 connection"""
        mt5.shutdown()
        self.connected = False
        logger.info("MT5 connection closed")
