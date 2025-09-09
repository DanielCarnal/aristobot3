# Batch Cancel Existing Order and Send New Orders - Bitget Spot Trading API

**Rate limit:** 5 requests/second/UID

## Description

Cancel an Existing Order and Send a New Order

## HTTP Request

**POST** `/api/v2/spot/trade/batch-cancel-replace-order`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/batch-cancel-replace-order" \
-H "ACCESS-KEY:*******" \
-H "ACCESS-SIGN:*******" \
-H "ACCESS-PASSPHRASE:*****" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json" \
-d '{
  "orderList": [
    {
      "orderId":"xxxxxxxxxxxxxxxxx",
      "clientOid":"",
      "symbol": "BTCUSDT",
      "price":"3.17",
      "size":"5"
    }
  ]
}'
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderList` | Array | Yes | Collection of placing orders, **maximum length: 50** |

### orderList Array Elements

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | Yes | Trading pair name, e.g. BTCUSDT. All symbols can be returned by [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `price` | String | Yes | Limit price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `size` | String | Yes | Amount, it represents the number of **base coins** |
| `clientOid` | String | No | Client Order ID. Either `orderId` or `clientOid` is required |
| `orderId` | String | No | Order ID. Either `orderId` or `clientOid` is required |
| `newClientOid` | String | No | New custom order ID. If `newClientOid` results in idempotency duplication, it may cause the old order to be successfully canceled but the new order placement to fail |
| `presetTakeProfitPrice` | String | No | Take profit price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `executeTakeProfitPrice` | String | No | Take profit execute price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `presetStopLossPrice` | String | No | Stop loss price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `executeStopLossPrice` | String | No | Stop loss execute price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1725341809524,
  "data": [
    {
      "orderId": "xxxxxxxxxxxxxxxxxxxxxx",
      "clientOid": null,
      "success": "failure",
      "msg": "xxxxxx"
    }
  ]
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `orderId` | String | Order ID |
| `clientOid` | String | Client Order ID |
| `success` | String | Operation success<br>• `success`: success<br>• `failure`: failure |
| `msg` | String | Failure reason |

## Important Notes

### Batch Processing

- **Maximum 50 orders** can be processed in a single request
- Each order in the batch is processed independently
- The response will contain results for each order in the same order as the request

### Order Identification (Per Order)

- **Either `orderId` or `clientOid` is required** for each order to identify the order to cancel
- Use `orderId` for system-generated order IDs
- Use `clientOid` for your custom order IDs

### New Order Parameters (Per Order)

- **`symbol`**: Must match the original order's trading pair
- **`price`**: New limit price for the replacement order
- **`size`**: New amount (number of base coins)
- **`newClientOid`**: Optional new custom ID for the replacement order

### Take Profit / Stop Loss (Per Order)

- Can set take profit and stop loss levels for each new order
- `presetTakeProfitPrice` / `presetStopLossPrice`: Trigger prices
- `executeTakeProfitPrice` / `executeStopLossPrice`: Execution prices

### Important Warnings

⚠️ **Idempotency Risk**: If `newClientOid` results in duplication, the old order may be canceled successfully but the new order placement may fail.

⚠️ **Partial Success**: Some orders in the batch may succeed while others fail. Check the `success` field for each order in the response.

### Rate Limits

- **5 requests per second per UID**

### Use Cases

1. **Bulk Price Adjustment**: Quickly modify prices of multiple existing orders
2. **Portfolio Rebalancing**: Replace multiple orders with new parameters
3. **Risk Management**: Add TP/SL to multiple existing orders
4. **Order Optimization**: Replace multiple orders with better parameters

### Best Practices

1. **Check Individual Results**: Always verify the `success` status for each order
2. **Handle Partial Failures**: Implement logic to retry failed orders if needed
3. **Stay Within Limits**: Don't exceed 50 orders per request
4. **Monitor Rate Limits**: Respect the 5 requests/second limit

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Batch-Cancel-Replace-Order*
