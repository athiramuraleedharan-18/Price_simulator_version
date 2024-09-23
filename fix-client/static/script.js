document.addEventListener('DOMContentLoaded', () => {
  const connectionStatus = document.getElementById('connection-status');
  const orderForm = document.getElementById('order-form');
  const orderConfirmation = document.getElementById('order-confirmation');
  const subscribeButton = document.getElementById('subscribe-market-data');
  const unsubscribeButton = document.getElementById('unsubscribe-market-data');
  const marketStatus = document.getElementById('market-status');
  const orderStatusForm = document.getElementById('order-status-form');
  const statusResponse = document.getElementById('status-response');
  const quantityInput = document.getElementById('quantity');
  
  // Simulate connection
  connectionStatus.textContent = 'Connection Status: Connected';
  connectionStatus.classList.remove('disconnected');
  connectionStatus.classList.add('connected');

  // Simulated exchange rates for USD/BRL and BRL/USD
  let exchangeRateUSD_BRL = 4.75; // Example: 1 USD = 4.75 BRL
  let exchangeRateBRL_USD = 1 / exchangeRateUSD_BRL; // Example: 1 BRL = ~0.21 USD

  // Function to calculate price based on quantity and symbol
  function calculatePrice() {
    const quantity = parseInt(document.getElementById('quantity').value);
    const priceField = document.getElementById('price');
    const symbol = document.getElementById('symbol').value;

    if (quantity && (symbol === 'USD/BRL' || symbol === 'BRL/USD')) {
        let totalPrice;
        if (symbol === 'USD/BRL') {
            // USD to BRL conversion
            totalPrice = quantity * exchangeRateUSD_BRL;
            priceField.value = `$ ${totalPrice.toFixed(2)}`; // Price in BRL
        } else if (symbol === 'BRL/USD') {
            // BRL to USD conversion
            totalPrice = quantity * exchangeRateBRL_USD;
            priceField.value = `$ ${totalPrice.toFixed(2)}`; // Price in USD
        }
    } else {
        priceField.value = ''; // Clear the price field if input is invalid
    }
  }

  // Add event listener to update price when quantity changes
  quantityInput.addEventListener('input', calculatePrice);

  // Handle order form submission
  orderForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const action = document.getElementById('action').value;
    const symbol = document.getElementById('symbol').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const price = document.getElementById('price').value;

    if (symbol === 'USD/BRL' || symbol === 'BRL/USD') {
        console.log(`Placing order: ${action}, Symbol: ${symbol}, Quantity: ${quantity}, Price: ${price}`);
        alert(`Order placed successfully at ${price}!`);
        orderConfirmation.textContent = 'Order placed successfully!';
        orderConfirmation.classList.remove('hidden');
        setTimeout(() => {
          orderConfirmation.classList.add('hidden');
        }, 3000);
    } else {
        alert('Please enter a valid currency pair (e.g., USD/BRL or BRL/USD).');
    }
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
    statusResponse.textContent = `Order ${clOrdId} status: In Progress`;
    statusResponse.classList.remove('hidden');
  });
});
