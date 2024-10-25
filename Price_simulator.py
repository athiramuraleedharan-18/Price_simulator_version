import quickfix as fix
import threading
import time
import random
import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
fix_app = None  # Global FIX application instance

class MarketTickerApplication(fix.Application):
    def __init__(self, instrument, initial_price):
        super().__init__()
        self.instrument = instrument
        self.price = initial_price
        self.price_subscribers = set()

    def onCreate(self, sessionID):
        logging.info(f"Session created: {sessionID}")

    def onLogon(self, sessionID):
        logging.info(f"Logon successful: {sessionID}")

    def onLogout(self, sessionID):
        logging.info(f"Logout: {sessionID}")
        self.price_subscribers.discard(sessionID)

    def toAdmin(self, message, sessionID):
        logging.debug(f"Sending admin message: {message}")

    def toApp(self, message, sessionID):
        logging.debug(f"Sending application message: {message}")

    def fromAdmin(self, message, sessionID):
        logging.debug(f"Received admin message: {message}")

    def fromApp(self, message, sessionID):
        logging.debug(f"Received application message: {message}")
        try:
            msg_type = message.getHeader().getField(fix.MsgType())
            if msg_type == fix.MsgType_MarketDataRequest:
                self.handle_market_data_request(message, sessionID)
        except fix.FieldNotFound as e:
            logging.error(f"Field not found: {e}")

    def handle_market_data_request(self, message, sessionID):
        subscription_type = message.getField(263)  # SubscriptionRequestType
        logging.info(f"Received subscription request from {sessionID}: {subscription_type}")
        
        if subscription_type == '1':  # Subscribe
            self.price_subscribers.add(sessionID)
            logging.info(f"Client {sessionID} subscribed to price updates.")
            self.send_price_snapshot(sessionID)  # Send initial price snapshot
        elif subscription_type == '2':  # Unsubscribe
            self.price_subscribers.discard(sessionID)
            logging.info(f"Client {sessionID} unsubscribed.")
        else:
            logging.info(f"Client {sessionID} requested a price snapshot.")
            self.send_price_snapshot(sessionID)

    def generate_prices(self):
        while True:
            self.price += random.uniform(-0.1, 0.1)  # Simulate price fluctuations
            self.price = max(0, self.price)  # Prevent negative prices
            self.broadcast_price()
            time.sleep(1)

    def broadcast_price(self):
        for session_id in self.price_subscribers:
            self.send_price_update(session_id)

    def send_price_update(self, session_id):
        price_message = self.create_price_message()
        self.send_message(price_message, session_id)

    def send_price_snapshot(self, session_id):
        price_message = self.create_price_message()
        self.send_message(price_message, session_id)

    def create_price_message(self):
        price_message = fix.Message()
        price_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        price_message.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataSnapshotFullRefresh))
        price_message.setField(55, self.instrument)
        price_message.setField(44, str(round(self.price, 4)))  # Round price to 4 decimal places
        return price_message

    def send_message(self, message, sessionID):
        try:
            fix.Session.sendToTarget(message, sessionID)
            logging.info(f"Sent message to {sessionID}: {message}")
        except fix.SessionNotFound:
            logging.error(f"Session not found for {sessionID}")

class ClientApplication(fix.Application):
    def __init__(self):
        super().__init__()
        self.sessionID = None

    def onCreate(self, session_id):
        logging.info(f"Session created: {session_id}")
        self.sessionID = session_id

    def onLogon(self, session_id):
        logging.info(f"Logon successful: {session_id}")
        self.sessionID = session_id  # Store session ID on successful logon

    def onLogout(self, session_id):
        logging.info(f"Logout: {session_id}")
        self.sessionID = None  # Clear session ID on logout

    def toAdmin(self, message, session_id):
        logging.info(f"Sending admin message: {message}")

    def toApp(self, message, session_id):
        logging.info(f"Sending application message: {message}")

    def fromAdmin(self, message, session_id):
        logging.info(f"Received admin message: {message}")

    def fromApp(self, message, session_id):
        logging.info(f"Received application message: {message}")
        # Here you can add any additional processing for incoming application messages

    def request_price_snapshot(self, instrument, subscription_request_type):
        # Check if the session is active
        if not self.sessionID or not fix.Session.lookupSession(self.sessionID).isLoggedOn():
            logging.warning("Session is not active, cannot send request.")
            return False  # No active session

        # Create a new FIX message for the price request
        request = fix.Message()
        request.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))  # Correctly set the BeginString
        request.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataRequest))
        request.setField(fix.MDReqID("1"))
        request.setField(fix.SubscriptionRequestType(subscription_request_type))
        request.setField(fix.MarketDepth(1))

        # Create a group for market data entry
        group = fix.Group(267, 55)  # Entry type group for Market Data Request
        group.setField(fix.MDEntryType('0'))  # Entry type (0 for bid)
        group.setField(fix.Symbol(instrument))
        request.addGroup(group)

        try:
            fix.Session.sendToTarget(request, self.sessionID)
            logging.info(f"Price request for {instrument} sent.")
            return True
        except fix.SessionNotFound as e:
            logging.error(f"Session not found: {e}")
            return False
        except Exception as e:
            logging.error(f"Error while sending price request: {e}")
            return False

def start_fix_server():
    global fix_app
    try:
        settings = fix.SessionSettings("server.cfg")
        fix_app = MarketTickerApplication("EUR/USD", 100.0)
        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.FileLogFactory(settings)
        acceptor = fix.SocketAcceptor(fix_app, store_factory, settings, log_factory)

        price_thread = threading.Thread(target=fix_app.generate_prices, daemon=True)
        price_thread.start()

        acceptor.start()
        logging.info("Server started...")

        # Keep server running
        while True:
            time.sleep(1)

    except Exception as e:
        logging.error(f"Error starting FIX server: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/request-price', methods=['POST'])
def request_price():
    data = request.json
    instrument = data.get('instrument')
    request_type = data.get('type', 'snapshot')
    subscription_request_type = '2' if request_type == 'updates' else '1'

    if fix_app and fix_app.sessionID and fix.Session.lookupSession(fix_app.sessionID).isLoggedOn():
        success = fix_app.request_price_snapshot(instrument, subscription_request_type)
        if success:
            return jsonify({'message': f"Price request for {instrument} sent successfully."}), 200
        else:
            return jsonify({'message': 'Failed to send the price request.'}), 500
    else:
        logging.warning("No active session found.")
        return jsonify({'message': 'No active FIX session found.'}), 404

if __name__ == "__main__":
    threading.Thread(target=start_fix_server).start()  # Start FIX server in a separate thread
    app.run(debug=True, host='0.0.0.0', port=5000)  # Run the Flask application
