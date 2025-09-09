# Bitget Spot Trading API Documentation

Complete documentation for all Bitget Spot Trading API endpoints.

## 📋 Overview

This documentation covers all the essential endpoints for spot trading on Bitget exchange, including order management, trade execution, and order history retrieval.

## 🔗 API Endpoints Documentation

### Order Management

| Endpoint | File | Description | Rate Limit |
|----------|------|-------------|------------|
| **Place Order** | [`place_order.md`](./place_order.md) | Create new spot trading orders | 10/sec (1/sec for copy traders) |
| **Cancel Order** | [`cancel_order.md`](./cancel_order.md) | Cancel a specific order | 10/sec |
| **Cancel Replace Order** | [`cancel_replace_order.md`](./cancel_replace_order.md) | Cancel existing order and place new one | 5/sec |
| **Cancel Order by Symbol** | [`cancel_order_by_symbol.md`](./cancel_order_by_symbol.md) | Cancel all orders for a trading pair | 5/sec |

### Batch Operations

| Endpoint | File | Description | Rate Limit |
|----------|------|-------------|------------|
| **Batch Place Orders** | [`batch_place_orders.md`](./batch_place_orders.md) | Place multiple orders (max 50) | 5/sec (1/sec for traders) |
| **Batch Cancel Orders** | [`batch_cancel_orders.md`](./batch_cancel_orders.md) | Cancel multiple orders (max 50) | 10/sec |
| **Batch Cancel Replace** | [`batch_cancel_replace_order.md`](./batch_cancel_replace_order.md) | Cancel and replace multiple orders | 5/sec |

### Order Information

| Endpoint | File | Description | Rate Limit |
|----------|------|-------------|------------|
| **Get Order Info** | [`get_order_info.md`](./get_order_info.md) | Get detailed info for specific order | 20/sec |
| **Get Current Orders** | [`get_current_orders.md`](./get_current_orders.md) | Get all unfilled orders | 20/sec |
| **Get History Orders** | [`get_history_orders.md`](./get_history_orders.md) | Get filled/cancelled orders | 20/sec |
| **Get Fills** | [`get_fills.md`](./get_fills.md) | Get trade execution details | 20/sec |

## 🚀 Quick Start

### Authentication
All endpoints require proper authentication headers:
```bash
-H "ACCESS-KEY:your_api_key"
-H "ACCESS-SIGN:signature"
-H "ACCESS-PASSPHRASE:passphrase"
-H "ACCESS-TIMESTAMP:timestamp"
-H "Content-Type: application/json"
```

### Base URL
```
https://api.bitget.com
```

## 📊 Order Types & Parameters

### Order Types
- **Limit Orders**: Specify exact price and quantity
- **Market Orders**: Execute immediately at market price
- **TP/SL Orders**: Take profit and stop loss orders

### Execution Strategies (force)
- **GTC**: Good Till Cancelled
- **IOC**: Immediate or Cancel
- **FOK**: Fill or Kill
- **POST_ONLY**: Post only (maker orders)

### Order Sides
- **buy**: Buy orders
- **sell**: Sell orders

## 💰 Amount Calculations

### Limit Orders & Market Sell
- `size` = amount of **base currency** (e.g., BTC in BTCUSDT)

### Market Buy Orders
- `size` = amount of **quote currency** (e.g., USDT in BTCUSDT)

## 🔄 Order Status Values

| Status | Description |
|--------|-------------|
| `live` | Order is pending match (open) |
| `partially_filled` | Order partially executed |
| `filled` | Order completely executed |
| `cancelled` | Order cancelled |

## ⚡ Rate Limits Summary

| Type | Standard | Copy Traders |
|------|----------|--------------|
| Place Order | 10/sec | 1/sec |
| Cancel Operations | 5-10/sec | 5-10/sec |
| Query Operations | 20/sec | 20/sec |
| Batch Operations | 5/sec | 1/sec |

## 🛡️ Best Practices

### 1. Error Handling
- Always check response codes
- Handle partial failures in batch operations
- Implement retry logic for failed orders

### 2. Rate Limit Management
- Monitor request frequency
- Implement backoff strategies
- Use batch operations when possible

### 3. Order Management
- Use `clientOid` for order tracking
- Check order status before modifications
- Handle race conditions (order fills during cancellation)

### 4. Security
- Keep API credentials secure
- Use IP whitelisting when possible
- Monitor API usage for anomalies

## 🔍 Common Use Cases

### 1. Basic Trading
```bash
# Place a limit buy order
POST /api/v2/spot/trade/place-order
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "orderType": "limit",
  "force": "gtc",
  "price": "45000",
  "size": "0.001"
}
```

### 2. Portfolio Management
```bash
# Get all current positions
GET /api/v2/spot/trade/unfilled-orders

# Cancel all orders for a symbol
POST /api/v2/spot/trade/cancel-symbol-order
{
  "symbol": "BTCUSDT"
}
```

### 3. Trade Analysis
```bash
# Get execution details
GET /api/v2/spot/trade/fills?orderId=123456789

# Get trading history
GET /api/v2/spot/trade/history-orders?symbol=BTCUSDT
```

## 🔧 Integration Tips

### 1. Order Lifecycle Tracking
1. Place order → Get `orderId`
2. Monitor with Get Order Info
3. Handle fills via Get Fills
4. Track completion via status changes

### 2. Risk Management
- Set appropriate TP/SL levels
- Monitor position sizes
- Use STP (Self Trade Prevention) when needed

### 3. Performance Optimization
- Use batch operations for multiple orders
- Filter queries by symbol and time range
- Implement efficient pagination

## 📚 Additional Resources

- [Bitget API Official Documentation](https://www.bitget.com/api-doc/spot/intro)
- [WebSocket Documentation](https://www.bitget.com/api-doc/spot/websocket/intro) (for real-time data)
- [Error Codes Reference](https://www.bitget.com/api-doc/spot/error-code)

## 📝 Support

- **Telegram**: [@bitgetOpenapi](https://t.me/bitgetOpenapi)
- **Official Support**: Check Bitget website for latest contact information

---

*Last Updated: September 2025*
*Documentation Version: v2.0*
