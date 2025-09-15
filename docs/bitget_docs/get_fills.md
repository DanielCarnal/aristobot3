# Get Fills - Bitget Spot Trading API

**Frequency limit:** 10 times/1s (UID)

## Description

Get Fills (It only supports to get the data within 90 days. The older data can be downloaded from web)

## HTTP Request

**GET** `/api/v2/spot/trade/fills`

### Request Example

```bash
curl "https://api.bitget.com/api/v2/spot/trade/fills?symbol=BTCUSDT&startTime=1659036670000&endTime=1659076670000&limit=20" \
  -H "ACCESS-KEY:your apiKey" \
  -H "ACCESS-SIGN:*" \
  -H "ACCESS-PASSPHRASE:*" \
  -H "ACCESS-TIMESTAMP:1659076670000" \
  -H "locale:en-US" \
  -H "Content-Type: application/json"
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | No | Trading pair name |
| `orderId` | String | No | Order ID |
| `startTime` | String | No | The start time of the orders, i.e. to get orders after that timestamp Unix millisecond timestamp, e.g. 1690196141868. (For Managed Sub-Account, the StartTime cannot be earlier than the binding time) |
| `endTime` | String | No | The end time of a fulfilled order, i.e., get orders prior to that timestamp Unix millisecond timestamp, e.g. 1690196141868 The interval between startTime and endTime must not exceed 90 days. |
| `limit` | String | No | Number of results returned: Default: 100, max 100 |
| `idLessThan` | String | No | Requests the content on the page before this ID (older data), the value input should be the tradeId of the corresponding interface. |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695865274510,
  "data": [
    {
      "userId": "**********",
      "symbol": "BTCUSDT",
      "orderId": "12345678910",
      "tradeId": "12345678910",
      "orderType": "market",
      "side": "buy",
      "priceAvg": "13000",
      "size": "0.0007",
      "amount": "9.1",
      "feeDetail": {
        "deduction": "no",
        "feeCoin": "BTC",
        "totalDeductionFee": "",
        "totalFee": "-0.0000007"
      },
      "tradeScope": "taker",
      "cTime": "1695865232579",
      "uTime": "1695865233027"
    }
  ]
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `userId` | String | Account ID |
| `symbol` | String | Trading pair name |
| `orderId` | String | Order ID |
| `tradeId` | String | Transaction id |
| `orderType` | String | Order type |
| `side` | String | Order direction |
| `priceAvg` | String | Filled price |
| `size` | String | Filled quantity |
| `amount` | String | Total trading amount |
| `cTime` | String | Creation time Unix second timestamp, e.g. 1622697148 |
| `uTime` | String | Update time Unix second timestamp, e.g. 1622697148 |
| `tradeScope` | String | Trader tag taker Taker maker Maker |
| `feeDetail` | Object | Transaction fee breakdown |
| `feeDetail.deduction` | String | Discount or not |
| `feeDetail.feeCoin` | String | Transaction fee coin |
| `feeDetail.totalDeductionFee` | String | Total transaction fee discount |
| `feeDetail.totalFee` | String | Total transaction fee |

## Important Notes

### Data Availability
- Only supports data retrieval within 90 days
- Older data can be downloaded from the web interface

### Time Range Constraints
- The interval between `startTime` and `endTime` must not exceed 90 days
- For Managed Sub-Account, the `startTime` cannot be earlier than the binding time

### Pagination
- Default limit: 100 results
- Maximum limit: 100 results per request
- Use `idLessThan` parameter with `tradeId` for pagination to get older data

### Rate Limits
- **10 requests per second per UID**

### Fee Information
- `feeDetail.totalFee`: Negative values typically indicate fees paid
- `feeDetail.deduction`: Indicates if fee discount was applied
- `feeDetail.feeCoin`: The cryptocurrency used to pay fees
- `feeDetail.totalDeductionFee`: Amount of fee discount received

### Trade Scope
- `taker`: Order that took liquidity from the order book
- `maker`: Order that added liquidity to the order book

### Use Cases

1. **Trade History Analysis**: Review all fill executions for trading analysis
2. **Fee Calculation**: Calculate total trading costs and fee structures
3. **Performance Tracking**: Monitor execution prices and trading performance
4. **Compliance Reporting**: Generate detailed trade records for regulatory purposes
5. **Order Reconstruction**: Understand how orders were filled in the market

### Query Examples

```bash
# Get recent fills for a specific symbol
GET /api/v2/spot/trade/fills?symbol=BTCUSDT

# Get fills for a specific order
GET /api/v2/spot/trade/fills?orderId=12345678910

# Get fills within a time range
GET /api/v2/spot/trade/fills?startTime=1659036670000&endTime=1659076670000

# Get fills with pagination
GET /api/v2/spot/trade/fills?idLessThan=12345678910&limit=50

# Get fills for multiple parameters
GET /api/v2/spot/trade/fills?symbol=BTCUSDT&startTime=1659036670000&limit=20
```

---

*Documentation based on official Bitget API specifications*