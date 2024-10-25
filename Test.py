import quickfix as fix
import quickfix44 as fix44  # FIX 4.4 version
import sys

class ClientApplication(fix.Application):
    def onCreate(self, sessionID):
        print(f"Session created: {sessionID}")
        
    def onLogon(self, sessionID):
        print(f"Logon - SessionID: {sessionID}")
        
    def onLogout(self, sessionID):
        print(f"Logout - SessionID: {sessionID}")
        
    def toAdmin(self, message, sessionID):
        print(f"Sending Admin Message: {message}")
        
    def fromAdmin(self, message, sessionID):
        print(f"Received Admin Message: {message}")
        
    def toApp(self, message, sessionID):
        print(f"Sending Application Message: {message}")
        try:
            fix.Session.sendToTarget(message, sessionID)
        except fix.SessionNotFound as e:
            print(f"Error: {e}")
        
    def fromApp(self, message, sessionID):
        print(f"Received Application Message: {message}")
        # Handle application-level messages here
        print(message)

# Function to run the FIX client
def start_fix_client():
    # Load the session settings from the config file
    settings = fix.SessionSettings("client.cfg")

    # Create an application instance
    application = ClientApplication()

    # Create a message store factory
    store_factory = fix.FileStoreFactory(settings)

    # Optionally create a log factory (use FileLogFactory for logging)
    log_factory = fix.FileLogFactory(settings)

    # Create a FIX initiator
    initiator = fix.SocketInitiator(application, store_factory, settings, log_factory)

    # Start the FIX client
    initiator.start()

    # Keep the client running
    try:
        while True:
            pass  # Replace with actual logic or handling for stopping the client
    except KeyboardInterrupt:
        print("Client shutting down.")
        initiator.stop()

if __name__ == "__main__":
    start_fix_client()
