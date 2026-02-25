from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
from signals.mt5_connector import MT5Connector
from signals.signal_generator import SignalGenerator
from config import Config
import logging

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
mt5_conn = MT5Connector(Config.MT5_LOGIN, Config.MT5_PASSWORD, Config.MT5_SERVER)
signal_gen = SignalGenerator()

# Store active connections and signals
active_signals = {}
connected_clients = set()

def update_signals():
    """Background thread to continuously update MT5 signals"""
    while True:
        try:
            for symbol in Config.SYMBOLS:
                # Get price data from MT5
                price_data = mt5_conn.get_price_data(symbol, Config.TIMEFRAME, Config.BARS_COUNT)
                
                if price_data is not None:
                    # Generate signal
                    signal = signal_gen.generate_signal(symbol, price_data)
                    active_signals[symbol] = signal
                    
                    # Broadcast to all connected clients
                    if connected_clients:
                        socketio.emit('signal_update', signal, broadcast=True)
                        logger.info(f"Signal updated for {symbol}: {signal['signal']}")
            
            time.sleep(Config.UPDATE_INTERVAL)
        except Exception as e:
            logger.error(f"Error updating signals: {str(e)}")
            time.sleep(Config.UPDATE_INTERVAL)

@app.route('/')
def index():
    """Serve the landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """REST endpoint to get current signals"""
    return jsonify(active_signals)

@app.route('/api/signal/<symbol>', methods=['GET'])
def get_signal(symbol):
    """REST endpoint to get signal for a specific symbol"""
    if symbol in active_signals:
        return jsonify(active_signals[symbol])
    return jsonify({'error': 'Symbol not found'}), 404

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'active_signals': len(active_signals),
        'connected_clients': len(connected_clients),
        'mt5_connected': mt5_conn.is_connected()
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    connected_clients.add(request.sid)
    logger.info(f"Client connected: {request.sid}")
    # Send current signals to new client
    socketio.emit('initial_signals', active_signals)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_symbol')
def handle_symbol_request(data):
    """Handle request for specific symbol data"""
    symbol = data.get('symbol')
    if symbol in active_signals:
        socketio.emit('signal_data', active_signals[symbol])

if __name__ == '__main__':
    # Start background signal update thread
    signal_thread = threading.Thread(target=update_signals, daemon=True)
    signal_thread.start()
    logger.info("Signal update thread started")
    
    # Start Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=Config.DEBUG)