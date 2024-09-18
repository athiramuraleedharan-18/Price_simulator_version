document.addEventListener('DOMContentLoaded', () => {
  const connectionStatus = document.getElementById('connection-status');
  const orderForm = document.getElementById('order-form');
  const subscribeButton = document.getElementById('subscribe-market-data');
  const unsubscribeButton = document.getElementById('unsubscribe-market-data');
  const orderStatusForm = document.getElementById('order-status-form');
  const orderConfirmation = document.getElementById('order-confirmation');
  const marketStatus = document.getElementById('market-status');
  const statusResponse = document.getElementById('status-response');

  // Establish WebSocket connection
  const socket = io();

  socket.on('connect', () => {
    console.log('Connected to server');
    connectionStatus.textContent = 'Connection Status: Connected';
    connectionStatus.classList.add('connected');
  });

  socket.on('market_data_update', (data) => {
    console.log('Received market data update:', data);
    // Update UI with new market data
    updateMarketDataUI(data);
  });

  function handleFetchResponse(response) {
    if (!response.ok) {
      return response.text().then(err => {
        throw new Error(err);
      });
    }
    return response.json();
  }

  function displayError(element, error) {
    console.error('Error:', error);
    element.textContent = `Error: ${error.message}`;
    element.classList.remove('hidden');
  }

  // Start client
  function startClient() {
    fetch('/start')
      .then(handleFetchResponse)
      .then(data => {
        connectionStatus.textContent = `Connection Status: ${data.status}`;
        connectionStatus.classList.add('connected');
        enableTradingUI();
      })
      .catch(error => displayError(connectionStatus, error));
  }

  // Handle order form submission
  orderForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const action = document.getElementById('action').value;
    const symbol = document.getElementById('symbol').value;
    const quantity = parseInt(document.getElementById('quantity').value);

    if (symbol && quantity > 0) {
      placeOrder(action, symbol, quantity);
    } else {
      alert('Please enter valid order details.');
    }
  });

  function placeOrder(action, symbol, quantity) {
    fetch('/order', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ action, symbol, quantity }),
    })
    .then(handleFetchResponse)
    .then(data => {
      orderConfirmation.textContent = data.status;
      orderConfirmation.classList.remove('hidden');
      updateOrderUI(data);
    })
    .catch(error => displayError(orderConfirmation, error));
  }

  // Handle subscribe button click
  subscribeButton.addEventListener('click', () => {
    const symbol = document.getElementById('symbol').value;
    subscribeMarketData(symbol);
  });

  function subscribeMarketData(symbol) {
    fetch('/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol }),
    })
    .then(handleFetchResponse)
    .then(data => {
      marketStatus.textContent = data.status;
      updateSubscriptionUI(true);
      marketStatus.classList.remove('hidden');
    })
    .catch(error => displayError(marketStatus, error));
  }

  // Handle unsubscribe button click
  unsubscribeButton.addEventListener('click', unsubscribeMarketData);

  function unsubscribeMarketData() {
    fetch('/unsubscribe', {
      method: 'POST',
    })
    .then(handleFetchResponse)
    .then(data => {
      marketStatus.textContent = data.status;
      updateSubscriptionUI(false);
      marketStatus.classList.remove('hidden');
    })
    .catch(error => displayError(marketStatus, error));
  }

  // Handle order status form submission
  orderStatusForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const clOrdID = document.getElementById('cl_ord_id').value;

    if (clOrdID) {
      requestOrderStatus(clOrdID);
    } else {
      alert('Please enter a valid ClOrdID.');
    }
  });

  function requestOrderStatus(cl_ord_id) {
    fetch('/order-status', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ cl_ord_id }),
    })
    .then(handleFetchResponse)
    .then(data => {
      statusResponse.textContent = data.status;
      statusResponse.classList.remove('hidden');
      updateOrderStatusUI(data);
    })
    .catch(error => displayError(statusResponse, error));
  }

  // UI update functions
  function updateMarketDataUI(data) {
    // Update market data display
    console.log('Updating market data display:', data);
    // Implement this based on your UI structure
  }

  function enableTradingUI() {
    // Enable trading buttons/forms
    orderForm.disabled = false;
    subscribeButton.disabled = false;
    orderStatusForm.disabled = false;
  }

  function updateOrderUI(data) {
    // Update order display
    console.log('Updating order display:', data);
    // Implement this based on your UI structure
  }

  function updateSubscriptionUI(isSubscribed) {
    subscribeButton.disabled = isSubscribed;
    unsubscribeButton.disabled = !isSubscribed;
  }

  function updateOrderStatusUI(data) {
    // Update order status display
    console.log('Updating order status display:', data);
    // Implement this based on your UI structure
  }

  // Start the client when the page loads
  startClient();
});