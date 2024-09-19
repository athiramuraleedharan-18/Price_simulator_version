document.addEventListener('DOMContentLoaded', () => {
  const connectionStatus = document.getElementById('connection-status');
  const orderForm = document.getElementById('order-form');
  const orderConfirmation = document.getElementById('order-confirmation');
  const subscribeButton = document.getElementById('subscribe-market-data');
  const unsubscribeButton = document.getElementById('unsubscribe-market-data');
  const marketStatus = document.getElementById('market-status');
  const orderStatusForm = document.getElementById('order-status-form');
  const statusResponse = document.getElementById('status-response');

  // Simulate connection
  connectionStatus.textContent = 'Connection Status: Connected';
  connectionStatus.classList.remove('disconnected');
  connectionStatus.classList.add('connected');

  // Handle order form submission
  orderForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const action = document.getElementById('action').value;
    const symbol = document.getElementById('symbol').value;
    const quantity = document.getElementById('quantity').value;

    console.log(`Placing order: ${action}, Symbol: ${symbol}, Quantity: ${quantity}`);

    // Simulate order placement
    orderConfirmation.textContent = 'Order placed successfully!';
    orderConfirmation.classList.remove('hidden');
    setTimeout(() => {
      orderConfirmation.classList.add('hidden');
    }, 3000);
  });

  // Handle market data subscription
  subscribeButton.addEventListener('click', () => {
    console.log('Subscribing to market data');
    marketStatus.textContent = 'Subscribed to market data';
    subscribeButton.disabled = true;
    unsubscribeButton.disabled = false;
  });

  unsubscribeButton.addEventListener('click', () => {
    console.log('Unsubscribing from market data');
    marketStatus.textContent = 'No market data subscribed';
    subscribeButton.disabled = false;
    unsubscribeButton.disabled = true;
  });

  // Handle order status check
  orderStatusForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const clOrdId = document.getElementById('cl_ord_id').value;

    console.log(`Checking status for order: ${clOrdId}`);

    // Simulate order status check
    statusResponse.textContent = `Order ${clOrdId} status: In Progress`;
    statusResponse.classList.remove('hidden');
  });
});
