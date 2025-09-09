# Cancel Order - Bitget Spot Trading API

**Rate limit:** 10 requests/second/UID

## Description

Cancel Order

## HTTP Request

**POST** `/api/v2/spot/trade/cancel-order`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/cancel-order" \
-H "ACCESS-KEY:*******" \
-H "ACCESS-SIGN:*" \
-H "ACCESS-PASSPHRASE:*" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json" \
-d '{
  "symbol": "BTCUSDT",
  "orderId": "121211212122"
}'
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | Yes | Trading pair name, e.g. BTCUSDT. It is not required when `tpslType` is `tpsl` |
| `tpslType` | String | No | Order type, default: `normal`<br>• `normal`: spot order<br>• `tpsl`: spot TP/SL order |
| `orderId` | String | No | Order ID. Either `orderId` or `clientOid` is required. It's required when `tpslType` is `tpsl` |
| `clientOid` | String | No | Client Order ID. Either `orderId` or `clientOid` is required |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1234567891234,
  "data": {
    "orderId": "121211212122",
    "clientOid": "xx001"
  }
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `orderId` | String | Order ID |
| `clientOid` | String | Client Order ID |

## Important Notes

### Order Identification

- **Either `orderId` or `clientOid` is required** to identify the order to cancel
- Use `orderId` for system-generated order IDs
- Use `clientOid` for your custom order IDs

### Order Types

1. **Normal Spot Orders (`tpslType=normal` or omitted)**:
   - Requires `symbol` parameter
   - Standard spot trading orders

2. **TP/SL Orders (`tpslType=tpsl`)**:
   - `symbol` parameter is not required
   - `orderId` is mandatory for TP/SL orders
   - Used for take profit and stop loss orders

### Rate Limits

- **10 requests per second per UID**

### Use Cases

1. **Cancel Single Order**: Cancel a specific order by ID
2. **Cancel TP/SL Orders**: Cancel take profit or stop loss orders
3. **Order Management**: Remove unwanted orders from the order book
4. **Risk Management**: Quickly cancel orders in volatile conditions

### Error Handling

Common reasons for cancellation failure:
- Order already filled
- Order already canceled
- Invalid order ID
- Order not found
- Insufficient permissions

### Best Practices

1. **Check Order Status**: Verify order exists before attempting to cancel
2. **Handle Race Conditions**: Order may fill between status check and cancellation
3. **Use Appropriate Identifiers**: Use `orderId` for system IDs, `clientOid` for custom IDs
4. **Monitor Rate Limits**: Stay within the 10 requests/second limit

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Cancel-Order*
