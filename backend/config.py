import os
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # MT5 Credentials
    MT5_LOGIN = int(os.getenv('MT5_LOGIN', 0))
    MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
    MT5_SERVER = os.getenv('MT5_SERVER', '')
    
    # Trading Configuration
    SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
    TIMEFRAME = mt5.TIMEFRAME_H1
    BARS_COUNT = 100
    UPDATE_INTERVAL = 300
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False