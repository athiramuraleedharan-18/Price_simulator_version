from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from Client import Client
from Market_maker import MarketMaker
import quickfix as fix
import traceback
import logging
from functools import wraps

app = Flask(__name__)
socketio = SocketIO(app)
client = Client()
initiator = None

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
def send_market_data_update(self, data):
    # This function should be called whenever there's new market data
    # It should use the Flask-SocketIO emit function
    from app import socketio
    socketio.emit('market_data_update', data)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not initiator or not initiator.isLoggedOn():
            return jsonify({"error": "Not logged on to any session"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['GET'])
def start_client():
    global initiator
    try:
        if initiator is None or not initiator.isLoggedOn():
            settings = fix.SessionSettings("client.cfg")
            store_factory = fix.FileStoreFactory(settings)
            log_factory = fix.ScreenLogFactory(settings)
            initiator = fix.SocketInitiator(client, store_factory, settings, log_factory)
            initiator.start()
            logger.info("Client started successfully")
            return jsonify({"status": "Client started successfully"})
        else:
            logger.info("Client already running")
            return jsonify({"status": "Client already running"})
    except Exception as e:
        logger.error(f"Error starting client: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/order', methods=['POST'])
@login_required
def place_order():
    data = request.json
    action = data.get('action')
    symbol = data.get('symbol', 'USD/BRL')
    quantity = data.get('quantity', 100)

    try:
        if action == "buy":
            client.place_order(fix.Side_BUY, symbol, quantity)
        elif action == "sell":
            client.place_order(fix.Side_SELL, symbol, quantity)
        else:
            logger.warning(f"Invalid action: {action}")
            return jsonify({"error": "Invalid action"}), 400

        logger.info(f"Order placed successfully: {action} {quantity} {symbol}")
        return jsonify({"status": "Order placed successfully"})
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe_market_data():
    data = request.json
    symbol = data.get('symbol', 'USD/BRL')
    try:
        client.subscribe_market_data(symbol)
        logger.info(f"Subscribed to market data for {symbol}")
        return jsonify({"status": "Subscribed to market data"})
    except Exception as e:
        logger.error(f"Error subscribing to market data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe_market_data():
    try:
        client.cancel_market_data()
        logger.info("Unsubscribed from market data")
        return jsonify({"status": "Unsubscribed from market data"})
    except Exception as e:
        logger.error(f"Error unsubscribing from market data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/order-status', methods=['POST'])
@login_required
def order_status_request():
    data = request.json
    cl_ord_id = data.get('cl_ord_id')
    symbol = data.get('symbol', 'USD/BRL')
    side = data.get('side', fix.Side_BUY)
    try:
        client.order_status_request(cl_ord_id, symbol, side)
        logger.info(f"Order status request sent for ClOrdID: {cl_ord_id}")
        return jsonify({"status": "Order status request sent"})
    except Exception as e:
        logger.error(f"Error sending order status request: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

def send_market_data_update(data):
    socketio.emit('market_data_update', data)

if __name__ == '__main__':
    app.run(debug=True)
    socketio.run(app, debug=True)