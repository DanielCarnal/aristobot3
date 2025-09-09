# Batch Cancel Orders - Bitget Spot Trading API

**Rate limit:** 10 requests/second/UID

## Description

Cancel Orders in Batch

## HTTP Request

**POST** `/api/v2/spot/trade/batch-cancel-order`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/batch-cancel-order" \
-H "ACCESS-KEY:*******" \
-H "ACCESS-SIGN:*" \
-H "ACCESS-PASSPHRASE:*" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json" \
-d '{
  "symbol": "",
  "batchMode":"multiple",
  "orderList": [
    {
      "orderId":"121211212122",
      "symbol":"BTCUSDT",
      "clientOid":"121211212122"
    }
  ]
}'
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | No | Trading pair name, e.g. BTCUSDT |
| `batchMode` | String | No | Batch order mode<br>• `single`: single currency mode (default)<br>• `multiple`: cross-currency mode<br><br>If `single` mode, the symbol in orderList will be ignored<br>If `multiple` mode, the symbol in orderList is required and symbol outside orderList will be ignored |
| `orderList` | Array | Yes | Order ID List, **maximum length: 50** |

### orderList Array Elements

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | No | Trading pair name, e.g. BTCUSDT |
| `orderId` | String | No | Order ID. Either `orderId` or `clientOid` is required |
| `clientOid` | String | No | Client Order ID. Either `clientOid` or `orderId` is required |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": {
    "successList": [
      {
        "orderId": "121211212122",
        "clientOid": "121211212122"
      }
    ],
    "failureList": [
      {
        "orderId": "121211212122",
        "clientOid": "xxx001",
        "errorMsg": "duplicate clientOrderId"
      }
    ]
  }
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `successList` | Array | Successful order list |
| `> orderId` | String | Order ID |
| `> clientOid` | String | Client Order ID |
| `failureList` | Array | Failed order list |
| `> orderId` | String | Order ID |
| `> clientOid` | String | Client Order ID |
| `> errorMsg` | String | Error information |
| `> errorCode` | String | Error code |

## Important Notes

### Batch Modes

1. **Single Currency Mode (`batchMode=single`)** - Default:
   - All orders in the batch belong to the same trading pair specified in the main `symbol` parameter
   - Individual `symbol` fields in orderList are ignored
   - Suitable for canceling multiple orders on one trading pair

2. **Cross-Currency Mode (`batchMode=multiple`)**:
   - Each order can belong to a different trading pair
   - The `symbol` field in each order is required
   - Main `symbol` parameter is ignored
   - Suitable for canceling orders across multiple trading pairs

### Order Identification

- **Either `orderId` or `clientOid` is required** for each order to identify the order to cancel
- Use `orderId` for system-generated order IDs
- Use `clientOid` for your custom order IDs

### Batch Processing

- **Maximum 50 orders** can be processed in a single request
- Each order is processed independently
- Some orders may succeed while others fail
- Check both `successList` and `failureList` in the response

### Rate Limits

- **10 requests per second per UID**

### Use Cases

1. **Risk Management**: Quickly cancel multiple orders during volatile conditions
2. **Strategy Adjustment**: Cancel a grid of orders to readjust strategy
3. **Portfolio Management**: Cancel orders across multiple trading pairs
4. **Order Cleanup**: Remove stale or unwanted orders

### Error Handling

Common reasons for cancellation failure:
- Order already filled
- Order already canceled
- Invalid order ID
- Order not found
- Insufficient permissions
- Order belongs to different trading pair (in single mode)

### Best Practices

1. **Check Both Lists**: Always examine both `successList` and `failureList`
2. **Handle Partial Failures**: Implement retry logic for failed cancellations if needed
3. **Validate Order IDs**: Ensure order IDs are correct before sending
4. **Use Appropriate Mode**: Choose `single` for same-pair orders, `multiple` for cross-pair
5. **Stay Within Limits**: Don't exceed 50 orders per request
6. **Monitor Rate Limits**: Respect the 10 requests/second limit

### Common Error Scenarios

- Order already executed or canceled
- Invalid order ID format
- Order belongs to different account
- Network timeout during processing
- Mismatched trading pair in single mode

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Batch-Cancel-Orders*
