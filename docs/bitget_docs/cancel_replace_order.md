# Cancel an Existing Order and Send a New Order - Bitget Spot Trading API

**Rate limit:** 5 requests/second/UID

## Description

Cancel an Existing Order and Send a New Order

## HTTP Request

**POST** `/api/v2/spot/trade/cancel-replace-order`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/cancel-replace-order" \
   -H "ACCESS-KEY:*******" \
   -H "ACCESS-SIGN:*******" \
   -H "ACCESS-PASSPHRASE:*****" \
   -H "ACCESS-TIMESTAMP:1659076670000" \
   -H "locale:en-US" \
   -H "Content-Type: application/json" \  
   -d '{
    "orderId":"xxxxxxxxxxxxxxx",
    "clientOid":"",
    "symbol": "BTCUSDT",
    "price":"3.24",
    "size":"4"
}'
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | Yes | Trading pair name, e.g. BTCUSDT. All symbols can be returned by Get Symbol Info interface |
| `price` | String | Yes | Limit price. The decimal places of price and the price step can be returned by the Get Symbol Info interface |
| `size` | String | Yes | Amount, it represents the number of **base coins** |
| `clientOid` | String | No | Client Order ID. Either `orderId` or `clientOid` is required |
| `orderId` | String | No | Order ID. Either `orderId` or `clientOid` is required |
| `newClientOid` | String | No | New customed order ID. If `newClientOid` results in idempotency duplication, it may cause the old order to be successfully canceled but the new order placement to fail |
| `presetTakeProfitPrice` | String | No | Take profit price. The decimal places of price and the price step can be returned by the Get Symbol Info interface |
| `executeTakeProfitPrice` | String | No | Take profit execute price. The decimal places of price and the price step can be returned by the Get Symbol Info interface |
| `presetStopLossPrice` | String | No | Stop loss price. The decimal places of price and the price step can be returned by the Get Symbol Info interface |
| `executeStopLossPrice` | String | No | Stop loss execute price. The decimal places of price and the price step can be returned by the Get Symbol Info interface |

## Response Example

```json
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1725345009763,
    "data": {
        "orderId": "xxxxxxxxxxxxxxx",
        "clientOid": null,
        "success": "success",
        "msg": null
    }
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

### Order Identification

- **Either `orderId` or `clientOid` is required** to identify the order to cancel
- Use `orderId` for system-generated order IDs
- Use `clientOid` for your custom order IDs

### New Order Parameters

- **`symbol`**: Must match the original order's trading pair
- **`price`**: New limit price for the replacement order
- **`size`**: New amount (number of base coins)
- **`newClientOid`**: Optional new custom ID for the replacement order

### Take Profit / Stop Loss

- Can set take profit and stop loss levels for the new order
- `presetTakeProfitPrice` / `presetStopLossPrice`: Trigger prices
- `executeTakeProfitPrice` / `executeStopLossPrice`: Execution prices

### Important Warnings

⚠️ **Idempotency Risk**: If `newClientOid` results in duplication, the old order may be canceled successfully but the new order placement may fail.

### Rate Limits

- **5 requests per second per UID**

### Use Cases

1. **Price Adjustment**: Quickly modify the price of an existing order
2. **Size Modification**: Change the order quantity
3. **Add TP/SL**: Add take profit or stop loss to an existing order
4. **Order Optimization**: Replace an order with better parameters

### Error Handling

- Check the `success` field in the response data
- If `success` is "failure", check the `msg` field for the error reason
- The operation may partially succeed (cancel but not place new order)

### Best Practices

1. Always verify the response to ensure both cancellation and new order placement succeeded
2. Use `newClientOid` carefully to avoid idempotency issues
3. Ensure the new order parameters are valid before calling this endpoint
4. Monitor rate limits to avoid being throttled

---

*Documentation based on Bitget API specifications*