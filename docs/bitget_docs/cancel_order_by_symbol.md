# Cancel Order by Symbol - Bitget Spot Trading API

**Rate limit:** 5 requests/second/UID

## Description

Cancel order by symbol

## HTTP Request

**POST** `/api/v2/spot/trade/cancel-symbol-order`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/cancel-symbol-order" \
-H "ACCESS-KEY:*******" \
-H "ACCESS-SIGN:*" \
-H "ACCESS-PASSPHRASE:*" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json" \
-d '{
  "symbol": "BTCUSDT"
}'
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | Yes | Trading pair name, e.g. BTCUSDT |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1698313139948,
  "data": {
    "symbol": "BGBUSDT"
  }
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | String | Cancelled symbol (This request is executed asynchronously. If you need to know the result, please query the Get History Orders endpoint.) |

## Important Notes

### Asynchronous Operation

⚠️ **This request is executed asynchronously**. The API will return a success response immediately, but the actual cancellation may take some time to complete.

### Verification

- To verify the cancellation results, use the **Get History Orders** endpoint
- Check the order status to confirm which orders were successfully cancelled

### Scope

- **Cancels ALL open orders** for the specified trading pair
- This includes both buy and sell orders
- Only affects orders that are currently open (not filled or already cancelled)

### Rate Limits

- **5 requests per second per UID**

### Use Cases

1. **Emergency Stop**: Quickly cancel all orders for a specific trading pair
2. **Strategy Reset**: Clear all orders before implementing a new strategy
3. **Risk Management**: Cancel all exposure to a specific asset
4. **Market Volatility**: Quickly exit all positions during extreme market conditions

### Important Warnings

⚠️ **Use with Caution**: This endpoint cancels ALL open orders for the specified symbol. Make sure this is your intended action.

⚠️ **Irreversible**: Once executed, you cannot undo this operation. All open orders for the symbol will be cancelled.

### Best Practices

1. **Double Check Symbol**: Ensure you're cancelling orders for the correct trading pair
2. **Verify Results**: Always check the Get History Orders endpoint to confirm cancellations
3. **Consider Timing**: Be aware that this is an asynchronous operation
4. **Risk Assessment**: Use this endpoint carefully in automated systems
5. **Monitor Rate Limits**: Respect the 5 requests/second limit

### Error Handling

Common scenarios:
- Invalid trading pair symbol
- No open orders to cancel
- Network timeout (operation may still succeed)
- Insufficient permissions

### Alternative Approaches

If you need more granular control:
- Use **Cancel Order** for individual orders
- Use **Batch Cancel Orders** for specific orders
- Use **Get Current Orders** first to see what orders exist

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Cancel-Symbol-Orders*
