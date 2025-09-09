# Get Current Orders - Bitget Spot Trading API

**Rate limit:** 20 requests/second/UID

## Description

Get Unfilled Orders

## HTTP Request

**GET** `/api/v2/spot/trade/unfilled-orders`

### Request Example

```bash
curl "https://api.bitget.com/api/v2/spot/trade/unfilled-orders?symbol=BTCUSDT&startTime=1659036670000&endTime=1659076670000&limit=20" \
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
| `startTime` | String | No | The record start time for the query. Unix millisecond timestamp, e.g. 1690196141868 |
| `endTime` | String | No | The end time of the record for the query. Unix millisecond timestamp, e.g. 1690196141868 |
| `idLessThan` | String | No | Requests the content on the page before this ID (older data), the value input should be the orderId of the corresponding interface |
| `limit` | String | No | Limit number default 100 max 100 |
| `orderId` | String | No | OrderId |
| `tpslType` | String | No | Order type default `normal`<br>• `normal`: spot order<br>• `tpsl`: spot TP/SL order |
| `requestTime` | String | No | Request Time, Unix millisecond timestamp |
| `receiveWindow` | String | No | Valid window period, Unix millisecond timestamp |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": [
    {
      "userId": "**********",
      "symbol": "btcusdt",
      "orderId": "2222222",
      "clientOid": "xxxxxxx",
      "priceAvg": "34829.12",
      "size": "1",
      "orderType": "limit",
      "side": "buy",
      "status": "new",
      "basePrice": "0",
      "baseVolume": "0",
      "quoteVolume": "0",
      "enterPointSource": "WEB",
      "presetTakeProfitPrice": "70000",
      "executeTakeProfitPrice": "",
      "presetStopLossPrice": "10000",
      "executeStopLossPrice": "",
      "cTime": "1622697148",
      "tpslType": "normal",
      "triggerPrice": null
    }
  ]
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `userId` | String | User ID |
| `symbol` | String | Trading pair name |
| `orderId` | String | Order ID |
| `clientOid` | String | Client order ID |
| `priceAvg` | String | Order price |
| `size` | String | Amount (`orderType=limit` means base coin; `orderType=market` means quote coin) |
| `orderType` | String | Order type<br>• `limit`: Limit price<br>• `market`: Market price |
| `side` | String | Direction |
| `status` | String | Order status<br>• `live`: unfilled<br>• `partially_filled`: partially filled<br>• `filled`: filled<br>• `cancelled`: cancelled |
| `basePrice` | String | Filled price |
| `baseVolume` | String | Filled volume in base coin |
| `quoteVolume` | String | Filled volume in quote coin |
| `enterPointSource` | String | Client type<br>• `WEB`: Web Client<br>• `APP`: App Client<br>• `API`: API Client<br>• `SYS`: System Client<br>• `ANDROID`: Android Client<br>• `IOS`: iOS Client |
| `orderSource` | String | Order source<br>• `normal`: Normal order<br>• `market`: Market order<br>• `spot_trader_buy`: Elite spot trade to buy (elite traders)<br>• `spot_follower_buy`: Copy trade to buy (followers)<br>• `spot_trader_sell`: Elite spot trade to sell (elite traders)<br>• `spot_follower_sell`: Copy trade to sell (followers)<br>• `strategy_oco_limit`: OCO orders |
| `presetTakeProfitPrice` | String | Take profit trigger price |
| `executeTakeProfitPrice` | String | Take profit execute price (If the value is empty, it means take profit in market price) |
| `presetStopLossPrice` | String | Stop loss trigger price |
| `executeStopLossPrice` | String | Stop loss execute price (If the value is empty, it means stop loss in market price) |
| `cTime` | String | Creation time, Unix millisecond timestamp, e.g. 1690196141868 |
| `uTime` | String | Update time, Unix millisecond timestamp, e.g. 1690196141868 |
| `triggerPrice` | String | Spot TP/SL trigger price (Only valid when `tpslType` is `tpsl`) |
| `tpslType` | String | • `normal`: spot order<br>• `tpsl`: spot TP/SL order |

## Important Notes

### Query Scope

- Returns **only unfilled orders** (status: `live` or `partially_filled`)
- Use **Get History Orders** for filled or cancelled orders

### Pagination

- **Default limit**: 100 orders
- **Maximum limit**: 100 orders per request
- Use `idLessThan` for pagination (older data)

### Filtering Options

1. **By Symbol**: Filter orders for specific trading pair
2. **By Time Range**: Use `startTime` and `endTime`
3. **By Order Type**: Use `tpslType` for normal vs TP/SL orders
4. **By Order ID**: Get specific order with `orderId`

### Order Status Values

- **`live`**: Order is open and waiting to be filled
- **`partially_filled`**: Order is partially executed

### Take Profit / Stop Loss

- **`presetTakeProfitPrice`**: TP trigger price
- **`executeTakeProfitPrice`**: TP execution price (empty = market price)
- **`presetStopLossPrice`**: SL trigger price  
- **`executeStopLossPrice`**: SL execution price (empty = market price)

### Rate Limits

- **20 requests per second per UID**

### Use Cases

1. **Portfolio Management**: View all open positions
2. **Order Monitoring**: Track order execution progress
3. **Risk Assessment**: Evaluate current exposure
4. **Strategy Adjustment**: Identify orders to modify or cancel
5. **Compliance**: Monitor trading activity

### Best Practices

1. **Efficient Filtering**: Use symbol filter for specific pairs
2. **Pagination**: Use `idLessThan` for large result sets
3. **Time Windows**: Use reasonable time ranges for better performance
4. **Regular Monitoring**: Check unfilled orders periodically
5. **Rate Limit Management**: Stay within 20 requests/second

### Common Query Patterns

```bash
# Get all unfilled orders
GET /api/v2/spot/trade/unfilled-orders

# Get unfilled orders for specific symbol
GET /api/v2/spot/trade/unfilled-orders?symbol=BTCUSDT

# Get recent unfilled orders (last 24 hours)
GET /api/v2/spot/trade/unfilled-orders?startTime=1690000000000

# Get unfilled TP/SL orders only
GET /api/v2/spot/trade/unfilled-orders?tpslType=tpsl

# Paginate through results
GET /api/v2/spot/trade/unfilled-orders?idLessThan=123456789&limit=50
```

### Error Handling

- Invalid symbol returns empty results
- Invalid time range may return no data
- Ensure proper authentication for private orders

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Get-Unfilled-Orders*
