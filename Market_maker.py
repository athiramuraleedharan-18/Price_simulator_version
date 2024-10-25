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
            elif msg_type in [fix.MsgType_NewOrderSingle, fix.MsgType_OrderCancelRequest]:
                self.handle_order_request(message, sessionID)
        except fix.FieldNotFound as e:
            logging.error(f"Field not found: {e}")

    def handle_order_request(self, message, sessionID):
        try:
            order_type = message.getField(fix.OrdType())  # Get order type
            symbol = message.getField(fix.Symbol())
            if symbol not in self.instruments:
                logging.error(f"Received order for unsupported instrument: {symbol}")
                self.send_order_reject(message, sessionID, "Unsupported Instrument")
                return
            price = message.getField(fix.Price()) if message.isSetField(fix.Price()) else None
            quantity = message.getField(fix.OrderQty())

            logging.info(f"Received order request: {order_type} {quantity} of {symbol} at {price if price else 'Market price'} from {sessionID}")

            if quantity <= 0:
                logging.error("Invalid order quantity")
                self.send_order_reject(message, sessionID, "Invalid Order Quantity")
                return

            if price is not None and price <= 0:
                logging.error("Invalid order price")
                self.send_order_reject(message, sessionID, "Invalid Order Price")
                return

            # Process the order based on the type
            if order_type == fix.OrdType_Market:
                self.execute_market_order(symbol, quantity)
            elif order_type == fix.OrdType_Limit:
                self.execute_limit_order(symbol, quantity, price)
            elif order_type == fix.OrdType_Stop:
                self.execute_stop_order(symbol, quantity, price)
            elif order_type == fix.OrdType_StopLimit:
                self.execute_stop_limit_order(symbol, quantity, price)

            # Send acknowledgment after processing
            self.send_order_acknowledgment(message, sessionID, fix.OrdStatus_NEW)

        except fix.FieldNotFound as e:
            logging.error(f"Error handling order request: {e}")
    
    def send_order_reject(self, message, sessionID, reason):
        # Sending order rejection message
        reject_message = fix.Message()
        reject_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        reject_message.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))
        
        reject_message.setField(fix.OrderID(str(random.randint(100000, 999999))))
        reject_message.setField(fix.ClOrdID(message.getField(fix.ClOrdID())))
        reject_message.setField(fix.Symbol(message.getField(fix.Symbol())))
        reject_message.setField(fix.OrdStatus(fix.OrdStatus_REJECTED))
        reject_message.setField(fix.Text(reason))

        self.send_message(reject_message, sessionID)

    def execute_market_order(self, symbol, quantity):
        logging.info(f"Executing Market Order: {quantity} of {symbol}")

    def execute_limit_order(self, symbol, quantity, price):
        logging.info(f"Executing Limit Order: {quantity} of {symbol} at {price}")

    def execute_stop_order(self, symbol, quantity, price):
        logging.info(f"Executing Stop Order: {quantity} of {symbol} at {price}")

    def execute_stop_limit_order(self, symbol, quantity, price):
        logging.info(f"Executing Stop Limit Order: {quantity} of {symbol} at {price}")

    def send_order_acknowledgment(self, message, sessionID, ord_status):
        # Create acknowledgment message as Execution Report
        ack_message = fix.Message()
        ack_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        ack_message.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))  # ExecutionReport for order acknowledgment

        # Set acknowledgment fields
        ack_message.setField(fix.OrderID(str(random.randint(100000, 999999))))  # Random Order ID
        ack_message.setField(fix.ClOrdID(message.getField(fix.ClOrdID())))  # Client Order ID
        ack_message.setField(fix.Symbol(message.getField(fix.Symbol())))  # Instrument
        ack_message.setField(fix.OrderQty(message.getField(fix.OrderQty())))  # Quantity
        ack_message.setField(fix.OrdStatus(ord_status))  # Order Status (e.g., NEW, FILLED, PARTIALLY_FILLED)
        ack_message.setField(fix.ExecType(fix.ExecType_NEW))  # Execution type: New order
        ack_message.setField(fix.Side(fix.Side_BUY))  # Assuming a buy order for this example
        ack_message.setField(fix.LeavesQty(message.getField(fix.OrderQty())))  # Remaining quantity
        ack_message.setField(fix.CumQty(0))  # No cumulative quantity at the moment

        # Send acknowledgment message
        self.send_message(ack_message, sessionID)

    def generate_prices(self):
        while True:
            for instrument in self.instruments:
                self.prices[instrument] += random.uniform(-0.1, 0.1)
                self.prices[instrument] = max(0.01, self.prices[instrument])  # Prevent prices <= 0
            self.broadcast_prices()
            time.sleep(self.price_frequency)

    def broadcast_prices(self):
        for session_id, subscribed_instruments in self.price_subscribers.items():
            for instrument in subscribed_instruments:
                self.send_price_update(session_id, instrument)

    def send_price_update(self, session_id, instrument):
        price_message = self.create_price_message(instrument)
        self.send_message(price_message, session_id)

    def create_price_message(self, instrument):
        price_message = fix.Message()
        price_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        price_message.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataSnapshotFullRefresh))
        
        # Set the price data
        price = self.prices[instrument]
        price_entry = fix.MDEntry()
        price_entry.setField(fix.MDEntryType(fix.MDEntryType_BID))  # Assuming we send the bid price
        price_entry.setField(fix.MDEntryPx(price))  # Set the price
        price_entry.setField(fix.MDEntrySize(100))  # Example size
        
        # Add entry to the message
        entry_group = fix.Group(268, 269)  # MDEntryType(269), MDEntryPx(271)
        entry_group.setField(price_entry.getField(fix.MDEntryType()))
        entry_group.setField(price_entry.getField(fix.MDEntryPx()))
        entry_group.setField(price_entry.getField(fix.MDEntrySize()))
        price_message.addGroup(entry_group)

        # Set the instrument information
        symbol = fix.Symbol(instrument)
        price_message.setField(symbol)

        return price_message

    def send_message(self, message, session_id):
        try:
            fix.Session.sendToTarget(message, session_id)
            logging.info(f"Sent message to {session_id}: {message}")
        except Exception as e:
            logging.error(f"Failed to send message to {session_id}: {e}")

def run_market_maker(instruments, initial_prices):
    app = MarketTickerApplication(instruments, initial_prices)
    threading.Thread(target=app.generate_prices, daemon=True).start()  # Start price generation in a separate thread

    settings = fix.SessionSettings("server.cfg")
    store_factory = fix.FileStoreFactory(settings)
    log_factory = fix.FileLogFactory(settings)
    acceptor = fix.SocketAcceptor(app, store_factory, settings, log_factory)

    acceptor.start()
    logging.info("Market Maker running...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        acceptor.stop()
        logging.info("Market Maker stopped.")

if __name__ == "__main__":    
    instruments = ["EUR/USD", "USD/JPY", "GBP/USD"]
    initial_prices = [121.1, 110.0, 120.75]
    run_market_maker(instruments, initial_prices)
