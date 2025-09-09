# Get History Orders - Bitget Spot Trading API

**Rate limit:** 20 requests/second/UID

## Description

Get History Orders (filled and cancelled orders)

## HTTP Request

**GET** `/api/v2/spot/trade/history-orders`

### Request Example

```bash
curl "https://api.bitget.com/api/v2/spot/trade/history-orders?symbol=BTCUSDT&startTime=1659036670000&endTime=1659076670000&limit=20" \
-H "ACCESS-KEY:*******" \
-H "ACCESS-SIGN:*" \
-H "ACCESS-PASSPHRASE:*" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json"
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | No | Trading pair |
| `startTime` | String | No | The record start time for the query. Unix millisecond timestamp |
| `endTime` | String | No | The end time of the record for the query. Unix millisecond timestamp |
| `idLessThan` | String | No | Requests the content on the page before this ID (older data), the value input should be the orderId |
| `limit` | String | No | Limit number default 100 max 100 |
| `orderId` | String | No | OrderId |
| `tpslType` | String | No | Order type default `normal`<br>• `normal`: spot order<br>• `tpsl`: spot TP/SL order |

## Response Structure

Returns an array of historical orders with the same structure as Get Current Orders, but includes orders with status:
- `filled`: Completely executed orders
- `cancelled`: Cancelled orders

## Important Notes

### Query Scope

- Returns **filled and cancelled orders only**
- Use **Get Current Orders** for active orders (`live`, `partially_filled`)

### Time Range

- **Maximum time range**: 90 days
- **Default behavior**: Returns recent history if no time range specified
- **Recommended**: Use reasonable time windows for better performance

### Pagination

- **Default limit**: 100 orders
- **Maximum limit**: 100 orders per request
- Use `idLessThan` for pagination to get older orders

### Rate Limits

- **20 requests per second per UID**

### Use Cases

1. **Trade History**: Review completed transactions
2. **Performance Analysis**: Calculate trading performance metrics
3. **Tax Reporting**: Generate transaction records for tax purposes
4. **Audit Trail**: Maintain compliance records
5. **Strategy Backtesting**: Analyze historical trading patterns

### Best Practices

1. **Use Time Filters**: Always specify time ranges for better performance
2. **Pagination**: Use `idLessThan` for accessing large historical datasets
3. **Symbol Filtering**: Filter by specific trading pairs when possible
4. **Batch Processing**: Process historical data in chunks
5. **Rate Limit Management**: Stay within 20 requests/second

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Get-History-Orders*
