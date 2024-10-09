import quickfix as fix
import quickfix44 as fix44

class MarketMakerApplication(fix.Application):
    def onCreate(self, sessionID):
        print(f"Session created: {sessionID}")

    def onLogon(self, sessionID):
        print(f"Logon: {sessionID}")

    def onLogout(self, sessionID):
        print(f"Logout: {sessionID}")

    def toAdmin(self, message, sessionID):
        # Print when sending admin messages, including heartbeats
        print(f"To Admin: {message}")
        
        # Check if the message is a heartbeat
        if message.getHeader().getField(fix.MsgType()) == fix.MsgType_Heartbeat:
            print(f"Sending Heartbeat: {message}")

    def fromAdmin(self, message, sessionID):
        # Print when receiving admin messages, including heartbeats
        print(f"From Admin: {message}")

        # Check if the message is a heartbeat
        if message.getHeader().getField(fix.MsgType()) == fix.MsgType_Heartbeat:
            print(f"Received Heartbeat: {message}")

    def toApp(self, message, sessionID):
        print(f"To App: {message}")

    def fromApp(self, message, sessionID):
        print(f"From App: {message}")

        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        print(f"Message Type: {msgType.getValue()}")  # Log the message type

        if msgType.getValue() == fix.MsgType_NewOrderSingle:
            self.process_new_order(message, sessionID)

    def process_new_order(self, message, sessionID):
        try:
            # Create field instances for retrieval
            symbol = fix.Symbol()
            side = fix.Side()
            orderQty = fix.OrderQty()
            price = fix.Price()

            # Retrieve fields from the message
            message.getField(symbol)
            message.getField(side)
            message.getField(orderQty)
            message.getField(price)

            # Debugging information
            print(f"Received new order: Symbol={symbol.getValue()}, Side={side.getValue()}, Qty={orderQty.getValue()}, Price={price.getValue()}")

            # Validate the symbol
            if not symbol.getValue():  # Check if symbol is empty
                print("Error: Symbol is empty.")
                return

            # Create and populate the Execution Report
            execution_report = fix44.ExecutionReport()
            execution_report.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))
            execution_report.setField(fix.OrderID("12345"))  # Unique Order ID
            execution_report.setField(fix.ExecID("54321"))    # Unique Execution ID
            execution_report.setField(fix.ExecType(fix.ExecType_FILL))
            execution_report.setField(fix.OrdStatus(fix.OrdStatus_FILLED))
            execution_report.setField(symbol)
            execution_report.setField(side)
            execution_report.setField(fix.LastShares(orderQty.getValue()))  # Quantity filled
            execution_report.setField(fix.LastPx(price.getValue()))        # Price of filled order
            execution_report.setField(fix.CumQty(orderQty.getValue()))      # Total quantity filled
            execution_report.setField(fix.AvgPx(price.getValue()))          # Average price of filled orders
            
            # Add LeavesQty (Tag 151) - the quantity left to be filled
            execution_report.setField(fix.LeavesQty(0))  # Assuming the order is fully filled, so 0 remains

            print(f"Sending Execution Report: {execution_report}")
            fix.Session.sendToTarget(execution_report, sessionID)
        except fix.FieldNotFound as e:
            print(f"Field not found error: {e}")
        except Exception as e:
            print(f"An error occurred while processing the order: {e}")

# Setup FIX engine
def start_marketmaker():
    settings = fix.SessionSettings("server.cfg")
    application = MarketMakerApplication()
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    acceptor = fix.SocketAcceptor(application, storeFactory, settings, logFactory)

    acceptor.start()

    input("Press <Enter> to stop...\n")
    acceptor.stop()

if __name__ == "__main__":
    start_marketmaker()
