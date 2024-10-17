import quickfix as fix
import threading
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MarketTickerApplication(fix.Application):
    def __init__(self, instruments, initial_prices, price_frequency=1):
        super().__init__()
        self.instruments = instruments
        self.prices = {instrument: price for instrument, price in zip(instruments, initial_prices)}
        self.price_subscribers = {}
        self.price_frequency = price_frequency

    def onCreate(self, sessionID):
        logging.info(f"Session created: {sessionID}")

    def onLogon(self, sessionID):
        logging.info(f"Logon successful: {sessionID}")
        self.price_subscribers[sessionID] = set()

    def onLogout(self, sessionID):
        logging.info(f"Logout: {sessionID}")
        self.price_subscribers.pop(sessionID, None)

    def toAdmin(self, message, sessionID):
        logging.debug(f"Sending admin message: {message}")
        logging.info(f"Outgoing Admin Message to {sessionID}: {message}")

    def toApp(self, message, sessionID):
        logging.debug(f"Sending application message: {message}")
        logging.info(f"Outgoing Application Message to {sessionID}: {message}")

    def fromAdmin(self, message, sessionID):
        logging.debug(f"Received admin message: {message}")
        logging.info(f"Incoming Admin Message from {sessionID}: {message}")

    def fromApp(self, message, sessionID):
        logging.debug(f"Received application message: {message}")
        logging.info(f"Incoming Application Message from {sessionID}: {message}")
        try:
            msg_type = message.getHeader().getField(fix.MsgType())
            if msg_type == fix.MsgType_MarketDataRequest:
                self.handle_market_data_request(message, sessionID)
        except fix.FieldNotFound as e:
            logging.error(f"Field not found: {e}")

    def handle_market_data_request(self, message, sessionID):
        try:
            subscription_type = message.getField(263)  # SubscriptionRequestType
            instrument = message.getField(55)  # Instrument symbol
            logging.info(f"Received subscription request for {instrument} from {sessionID}")

            if instrument not in self.instruments:
                logging.error(f"Instrument {instrument} is not tracked.")
                return  # Ignore invalid instruments

            if subscription_type == '1':  # Subscribe
                self.price_subscribers[sessionID].add(instrument)
                logging.info(f"Client {sessionID} subscribed to {instrument} updates.")
                self.send_price_snapshot(sessionID, instrument)
            elif subscription_type == '2':  # Unsubscribe
                self.price_subscribers[sessionID].discard(instrument)
                logging.info(f"Client {sessionID} unsubscribed from {instrument} updates.")
            else:
                logging.info(f"Client {sessionID} requested a price snapshot for {instrument}.")
                self.send_price_snapshot(sessionID, instrument)
        except fix.FieldNotFound as e:
            logging.error(f"Error handling market data request: {e}")

    def generate_prices(self):
        while True:
            for instrument in self.instruments:
                self.prices[instrument] += random.uniform(-0.1, 0.1)
                self.prices[instrument] = max(0, self.prices[instrument])  # Prevent negative prices
            self.broadcast_prices()
            time.sleep(self.price_frequency)

    def broadcast_prices(self):
        for session_id, subscribed_instruments in self.price_subscribers.items():
            for instrument in subscribed_instruments:
                self.send_price_update(session_id, instrument)

    def send_price_update(self, session_id, instrument):
        price_message = self.create_price_message(instrument)
        self.send_message(price_message, session_id)

    def send_price_snapshot(self, session_id, instrument):
        price_message = self.create_price_message(instrument)
        self.send_message(price_message, session_id)

    def create_price_message(self, instrument):
        price_message = fix.Message()
        price_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        price_message.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataSnapshotFullRefresh))
        price_message.setField(fix.MDReqID("1"))
        price_message.setField(fix.Symbol(instrument))
        price_message.setField(fix.MDEntryPx(self.prices[instrument]))
        return price_message

    def send_message(self, message, session_id):
        try:
            fix.Session.sendToTarget(message, session_id)
            logging.info(f"Price update for {message.getField(55)} sent to {session_id}")
        except fix.SessionNotFound as e:
            logging.error(f"Session not found: {e}")

def run_market_ticker(instruments, initial_prices, price_frequency=1):
    app = MarketTickerApplication(instruments, initial_prices, price_frequency)
    settings = fix.SessionSettings("server.cfg")
    store_factory = fix.FileStoreFactory(settings)
    acceptor = fix.SocketAcceptor(app, store_factory, settings)

    acceptor.start()
    app.generate_prices()

if __name__ == "__main__":
    instruments = ["EUR/USD", "USD/JPY", "GBP/USD"]  # Define your trading instruments
    initial_prices = [1.0, 110.0, 1.3]  # Starting prices for the instruments
    price_frequency = 2  # Set price update frequency to 2 seconds
    threading.Thread(target=run_market_ticker, args=(instruments, initial_prices, price_frequency)).start()
