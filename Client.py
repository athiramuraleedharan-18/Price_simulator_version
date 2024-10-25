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

        # Dropdown for instrument selection
        self.instrument_label = tk.Label(root, text="Select Instrument:")
        self.instrument_label.pack()

        self.instrument_var = tk.StringVar(root)
        self.instrument_var.set("EUR/USD")  # Default value

        self.instrument_dropdown = tk.OptionMenu(root, self.instrument_var, "EUR/USD", "USD/JPY", "GBP/USD")
        self.instrument_dropdown.pack()

        # Subscribe and Unsubscribe buttons
        self.subscribe_button = tk.Button(root, text="Subscribe", command=self.subscribe)
        self.subscribe_button.pack()

        self.unsubscribe_button = tk.Button(root, text="Unsubscribe", command=self.unsubscribe)
        self.unsubscribe_button.pack()

        # Price display area
        self.price_label = tk.Label(root, text="Price Updates:")
        self.price_label.pack()

        self.price_display = tk.Text(root, height=10, width=30)
        self.price_display.pack()

        # Section for placing orders
        self.order_label = tk.Label(root, text="Place Order:")
        self.order_label.pack()

        self.order_type_var = tk.StringVar(root)
        self.order_type_var.set("Market")  # Default order type

        self.order_type_dropdown = tk.OptionMenu(root, self.order_type_var, "Market", "Limit", "Stop", "Stop-Limit", command=self.update_order_fields)
        self.order_type_dropdown.pack()

        self.quantity_label = tk.Label(root, text="Quantity:")
        self.quantity_label.pack()
        self.quantity_entry = tk.Entry(root)
        self.quantity_entry.pack()

        # Order Price and Stop Price fields, initially hidden for Market orders
        self.order_price_label = tk.Label(root, text="Price:")
        self.order_price_label.pack()
        self.price_entry = tk.Entry(root)
        self.price_entry.pack()

        self.stop_price_label = tk.Label(root, text="Stop Price:")
        self.stop_price_label.pack()
        self.stop_price_entry = tk.Entry(root)
        self.stop_price_entry.pack()

        self.order_price_label.pack_forget()
        self.price_entry.pack_forget()
        self.stop_price_label.pack_forget()
        self.stop_price_entry.pack_forget()

        self.place_order_button = tk.Button(root, text="Place Order", command=self.place_order)
        self.place_order_button.pack()

        # Start polling the queue to update the GUI
        self.root.after(100, self.process_queue)

    def update_order_fields(self, order_type):
        """Update fields displayed based on the selected order type."""
        if order_type == "Market":
            self.order_price_label.pack_forget()
            self.price_entry.pack_forget()
            self.stop_price_label.pack_forget()
            self.stop_price_entry.pack_forget()
        elif order_type == "Limit":
            self.order_price_label.pack()
            self.price_entry.pack()
            self.stop_price_label.pack_forget()
            self.stop_price_entry.pack_forget()
        elif order_type == "Stop":
            self.order_price_label.pack_forget()
            self.price_entry.pack_forget()
            self.stop_price_label.pack()
            self.stop_price_entry.pack()
        elif order_type == "Stop-Limit":
            self.order_price_label.pack()
            self.price_entry.pack()
            self.stop_price_label.pack()
            self.stop_price_entry.pack()

    def subscribe(self):
        instrument = self.instrument_var.get()
        self.client_app.subscribe_to_price(instrument)
        logging.info(f"Subscribed to price updates for {instrument}")

    def unsubscribe(self):
        instrument = self.instrument_var.get()
        self.client_app.unsubscribe_from_price(instrument)
        logging.info(f"Unsubscribed from price updates for {instrument}")

    def place_order(self):
        instrument = self.instrument_var.get()
        quantity = int(self.quantity_entry.get())
        order_type = self.order_type_var.get()
        
        price = None
        stop_price = None

        if order_type == "Limit" or order_type == "Stop-Limit":
            price = float(self.price_entry.get())
        if order_type == "Stop" or order_type == "Stop-Limit":
            stop_price = float(self.stop_price_entry.get())

        self.client_app.send_order(instrument, quantity, order_type, price, stop_price)
        logging.info(f"Order placed: {order_type} order for {quantity} of {instrument} at {price} with stop price {stop_price}")

    def process_queue(self):
        while not self.queue.empty():
            msg = self.queue.get()
            self.price_display.insert(tk.END, msg + "\n")
            self.price_display.see(tk.END)
        self.root.after(100, self.process_queue)


class FIXClientApp(fix.Application):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def onCreate(self, sessionID):
        logging.info(f"Session created: {sessionID}")

    def onLogon(self, sessionID):
        logging.info(f"Logon successful: {sessionID}")

    def onLogout(self, sessionID):
        logging.info(f"Logout: {sessionID}")

    def toAdmin(self, message, sessionID):
        logging.debug(f"Sending admin message: {message}")

    def fromAdmin(self, message, sessionID):
        logging.debug(f"Received admin message: {message}")

    def toApp(self, message, sessionID):
        logging.debug(f"Sending application message: {message}")

    def fromApp(self, message, sessionID):
        logging.info(f"Incoming application message: {message}")
        self.gui.queue.put(str(message))

    def subscribe_to_price(self, instrument):
        message = fix.Message()
        message.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        message.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataRequest))

        message.setField(fix.Symbol(instrument))
        fix.Session.sendToTarget(message, self.sessionID)

    def unsubscribe_from_price(self, instrument):
        # Add logic to unsubscribe if needed
        pass

    def send_order(self, instrument, quantity, order_type, price=None, stop_price=None):
        order_msg = fix.Message()
        order_msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        order_msg.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))

        order_msg.setField(fix.ClOrdID(str(random.randint(100000, 999999))))
        order_msg.setField(fix.Symbol(instrument))
        order_msg.setField(fix.OrderQty(quantity))

        # Map order type to FIX order type
        order_type_map = {
            "Market": fix.OrdType_Market,
            "Limit": fix.OrdType_Limit,
            "Stop": fix.OrdType_Stop,
            "Stop-Limit": fix.OrdType_StopLimit
        }
        order_msg.setField(order_type_map[order_type])

        if price is not None:
            order_msg.setField(fix.Price(price))
        if stop_price is not None:
            order_msg.setField(fix.StopPx(stop_price))

        fix.Session.sendToTarget(order_msg, self.sessionID)


def run_client():
    root = tk.Tk()
    app = FIXClientApp(None)
    gui = FIXClientGUI(root, app)
    app.gui = gui

    settings = fix.SessionSettings("client.cfg")
    store_factory = fix.FileStoreFactory(settings)
    log_factory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(app, store_factory, settings, log_factory)

    initiator.start()
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()
    initiator.stop()


if __name__ == "__main__":
    run_client()
