import quickfix as fix
import tkinter as tk
from tkinter import messagebox
import threading
import queue
import random
import time
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FIXClientGUI:
    def __init__(self, root, client_app):
        self.root = root
        self.root.title("FIX Client GUI")
        self.client_app = client_app
        self.queue = queue.Queue()  # Queue for thread-safe communication

        # Create dropdown for instrument selection
        self.instrument_label = tk.Label(root, text="Select Instrument:")
        self.instrument_label.pack()

        self.instrument_var = tk.StringVar(root)
        self.instrument_var.set("EUR/USD")  # Default value

        self.instrument_dropdown = tk.OptionMenu(root, self.instrument_var, "EUR/USD", "USD/JPY", "GBP/USD")
        self.instrument_dropdown.pack()

        # Create subscribe button
        self.subscribe_button = tk.Button(root, text="Subscribe", command=self.subscribe)
        self.subscribe_button.pack()

        # Create unsubscribe button
        self.unsubscribe_button = tk.Button(root, text="Unsubscribe", command=self.unsubscribe)
        self.unsubscribe_button.pack()

        # Create price display area
        self.price_label = tk.Label(root, text="Price Updates:")
        self.price_label.pack()

        self.price_display = tk.Text(root, height=10, width=30)
        self.price_display.pack()

        # Start polling the queue to update the GUI
        self.root.after(100, self.process_queue)

    def subscribe(self):
        instrument = self.instrument_var.get()
        if instrument not in self.client_app.subscribed_instruments:
            self.client_app.subscribe_to_instrument(instrument)  # Use the FIX application to subscribe
            self.client_app.start_price_generation(instrument)  # Start generating prices for this instrument
            messagebox.showinfo("Subscribed", f"Subscribed to {instrument}")
        else:
            messagebox.showinfo("Already Subscribed", f"Already subscribed to {instrument}")

    def unsubscribe(self):
        instrument = self.instrument_var.get()
        if instrument in self.client_app.subscribed_instruments:
            self.client_app.unsubscribe_from_instrument(instrument)  # Use the FIX application to unsubscribe
            self.client_app.stop_price_generation(instrument)  # Stop generating prices for this instrument
            messagebox.showinfo("Unsubscribed", f"Unsubscribed from {instrument}")
        else:
            messagebox.showinfo("Not Subscribed", f"Not subscribed to {instrument}")

    def update_price_display(self, instrument, price):
        """Thread-safe method to update the price display."""
        self.queue.put(f"{instrument}: {price}\n")  # Place data in the queue

    def process_queue(self):
        """Process the queue and update the GUI."""
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                self.price_display.insert(tk.END, message)
                self.price_display.see(tk.END)
        except queue.Empty:
            pass
        # Continue polling the queue every 100ms
        self.root.after(100, self.process_queue)


class ClientApplication(fix.Application):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.session_id = None
        self.subscribed_instruments = set()  # Keep track of subscribed instruments
        self.price_threads = {}  # Store threads for price generation

    def onCreate(self, sessionID):
        logging.info(f"Session created: {sessionID}")
        self.session_id = sessionID

    def onLogon(self, sessionID):
        logging.info(f"Logon successful: {sessionID}")

    def onLogout(self, sessionID):
        logging.info(f"Logout: {sessionID}")

    def toAdmin(self, message, sessionID):
        pass

    def toApp(self, message, sessionID):
        logging.info(f"Sending message: {message}")  # Log outgoing message
        print(f"Outgoing: {message}")  # Print to terminal
        pass

    def fromAdmin(self, message, sessionID):
        pass

    def fromApp(self, message, sessionID):
        logging.info(f"Received message: {message}")  # Log incoming message
        print(f"Incoming: {message}")  # Print to terminal
        self.process_market_data(message)

    def subscribe_to_instrument(self, instrument):
        if self.session_id is not None:
            message = fix.Message()
            message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
            message.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataRequest))

            # Unique ID for the subscription request
            md_req_id = fix.MDReqID("SUBSCRIBE_" + instrument)
            message.setField(md_req_id)

            # Subscription type: Snapshot + Updates
            message.setField(fix.SubscriptionRequestType(fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES))

            # Specify the instrument
            symbol = fix.Symbol(instrument)
            instrument_group = fix.Group(146, 55)  # NoRelatedSym(146), Symbol(55)
            instrument_group.setField(symbol)
            message.addGroup(instrument_group)

            # Send the message via FIX
            fix.Session.sendToTarget(message, self.session_id)

            # Add the instrument to the subscribed list
            self.subscribed_instruments.add(instrument)

    def unsubscribe_from_instrument(self, instrument):
        if self.session_id is not None:
            message = fix.Message()
            message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
            message.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataRequest))

            # Unique ID for the unsubscription request
            md_req_id = fix.MDReqID("UNSUBSCRIBE_" + instrument)
            message.setField(md_req_id)

            # Unsubscribe (subscription type = unsubscribe)
            message.setField(fix.SubscriptionRequestType(fix.SubscriptionRequestType_DISABLE_PREVIOUS_SNAPSHOT_PLUS_UPDATE_REQUEST))

            # Specify the instrument
            symbol = fix.Symbol(instrument)
            instrument_group = fix.Group(146, 55)  # NoRelatedSym(146), Symbol(55)
            instrument_group.setField(symbol)
            message.addGroup(instrument_group)

            # Send the message via FIX
            fix.Session.sendToTarget(message, self.session_id)

            # Remove the instrument from the subscribed list
            self.subscribed_instruments.remove(instrument)

    def process_market_data(self, message):
        """Process market data updates and update the GUI"""
        try:
            # Extract the symbol (instrument) and the price from the FIX message
            instrument = fix.Symbol()
            price = fix.MDEntryPx()

            # Ensure that the message contains the required fields
            if message.isSetField(instrument) and message.isSetField(price):
                message.getField(instrument)
                message.getField(price)

                # Safely pass the update to the GUI thread
                self.gui.update_price_display(instrument.getValue(), price.getValue())
        except Exception as e:
            logging.error(f"Error processing market data: {e}")

    def start_price_generation(self, instrument):
        """Start a thread to generate prices for the subscribed instrument."""
        if instrument not in self.price_threads:
            thread = threading.Thread(target=self.generate_prices, args=(instrument,), daemon=True)
            self.price_threads[instrument] = thread
            thread.start()

    def stop_price_generation(self, instrument):
        """Stop generating prices for the unsubscribed instrument."""
        if instrument in self.price_threads:
            del self.price_threads[instrument]  # Remove the thread

    def generate_prices(self, instrument):
        """Simulate price updates for the subscribed instrument."""
        while instrument in self.subscribed_instruments:
            price = round(random.uniform(1.0, 1.5), 5)  # Random price generation
            self.gui.update_price_display(instrument, price)
            time.sleep(1)  # Sleep for a while before generating the next price


def run_client():
    # Initialize the GUI
    root = tk.Tk()

    # Initialize the FIX application with the GUI
    app = ClientApplication(None)
    gui = FIXClientGUI(root, app)
    app.gui = gui

    # Start the FIX engine in a separate thread
    threading.Thread(target=run_fix_engine, args=(app,), daemon=True).start()

    # Start the GUI
    root.mainloop()


def run_fix_engine(app):
    settings = fix.SessionSettings("client.cfg")
    store_factory = fix.FileStoreFactory(settings)
    log_factory = fix.FileLogFactory(settings)  # Make sure this is created
    initiator = fix.SocketInitiator(app, store_factory, settings, log_factory)  # Pass log_factory

    initiator.start()

    # Run the FIX engine until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        initiator.stop()

if __name__ == "__main__":
    run_client()
