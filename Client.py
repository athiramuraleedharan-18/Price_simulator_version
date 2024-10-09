import quickfix as fix
import quickfix44 as fix44

class ClientApplication(fix.Application):
    def onCreate(self, sessionID):
        print(f"Session created: {sessionID}")

    def onLogon(self, sessionID):
        print(f"Logon: {sessionID}")

    def onLogout(self, sessionID):
        print(f"Logout: {sessionID}")

    def toAdmin(self, message, sessionID):
        print(f"To Admin: {message}")

    def fromAdmin(self, message, sessionID):
        print(f"From Admin: {message}")

    def toApp(self, message, sessionID):
        print(f"To App: {message}")

    def fromApp(self, message, sessionID):
        print(f"From App: {message}")

        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        print(f"Message Type: {msgType.getValue()}")  # Log the message type

        if msgType.getValue() == fix.MsgType_ExecutionReport:
            self.process_execution_report(message, sessionID)
        elif msgType.getValue() == fix.MsgType_Heartbeat:
            print("Heartbeat received.")

    def process_execution_report(self, message, sessionID):
        try:
            # Create field instances for retrieval
            orderID = fix.OrderID()
            execID = fix.ExecID()
            ordStatus = fix.OrdStatus()
            lastShares = fix.LastShares()
            lastPx = fix.LastPx()

            # Retrieve fields from the message
            message.getField(orderID)
            message.getField(execID)
            message.getField(ordStatus)
            message.getField(lastShares)
            message.getField(lastPx)

            # Debugging information
            print(f"Received Execution Report: OrderID={orderID.getValue()}, "
                  f"ExecID={execID.getValue()}, Status={ordStatus.getValue()}, "
                  f"LastShares={lastShares.getValue()}, LastPx={lastPx.getValue()}")

        except fix.FieldNotFound as e:
            print(f"Field not found error: {e}")
        except Exception as e:
            print(f"An error occurred while processing the execution report: {e}")

# Setup FIX engine
def start_client():
    settings = fix.SessionSettings("client.cfg")
    application = ClientApplication()
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)

    initiator.start()

    input("Press <Enter> to stop...\n")
    initiator.stop()

if __name__ == "__main__":
    start_client()
