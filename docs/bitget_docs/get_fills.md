# Get Fills - Bitget Spot Trading API

**Rate limit:** 20 requests/second/UID

## Description

Get Fills (Trade executions and individual fill records)

## HTTP Request

**GET** `/api/v2/spot/trade/fills`

### Request Example

```bash
curl "https://api.bitget.com/api/v2/spot/trade/fills?symbol=BTCUSDT&startTime=1659036670000&endTime=1659076670000&limit=20" \
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
| `orderId` | String | No | Order ID |
| `startTime` | String | No | The record start time for the query. Unix millisecond timestamp |
| `endTime` | String | No | The end time of the record for the query. Unix millisecond timestamp |
| `idLessThan` | String | No | Requests the content on the page before this ID (older data), the value input should be the fillId |
| `limit` | String | No | Limit number default 100 max 100 |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": [
    {
      "fillId": "1234567890",
      "orderId": "987654321",
      "symbol": "BTCUSDT",
      "side": "buy",
      "fillPrice": "45000.50",
      "fillQuantity": "0.001",
      "fillTime": "1690196141868",
      "feeCcy": "BGB",
      "fees": "-0.045"
    }
  ]
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `fillId` | String | Fill ID (unique identifier for each trade execution) |
| `orderId` | String | Order ID |
| `symbol` | String | Trading pair name |
| `side` | String | Order direction (`buy` or `sell`) |
| `fillPrice` | String | Execution price for this fill |
| `fillQuantity` | String | Executed quantity for this fill (in base currency) |
| `fillTime` | String | Execution time, Unix millisecond timestamp |
| `feeCcy` | String | Fee currency |
| `fees` | String | Fee amount (negative value indicates fee paid) |

## Important Notes

### Fill vs Order Difference

- **Orders**: Individual trading instructions you place
- **Fills**: Individual executions that make up an order
- **One Order** can have **multiple Fills** if partially executed

### Fill Records

- Each fill represents a single trade execution
- Large orders may be split into multiple fills
- Each fill has its own execution price and quantity
- Useful for detailed trade analysis and fee calculation

### Time Range

- **Maximum time range**: 90 days
- **Default behavior**: Returns recent fills if no time range specified

### Pagination

- **Default limit**: 100 fills
- **Maximum limit**: 100 fills per request
- Use `idLessThan` with `fillId` for pagination

### Fee Information

- **`feeCcy`**: Currency in which fees are paid (often BGB for discounts)
- **`fees`**: Negative values indicate fees paid, positive values indicate rebates
- Fees are per fill, not per order

### Rate Limits

- **20 requests per second per UID**

### Use Cases

1. **Detailed Trade Analysis**: Analyze execution quality and slippage
2. **Fee Calculation**: Calculate total trading costs per order
3. **Performance Metrics**: Measure execution efficiency
4. **Compliance Reporting**: Detailed trade records for regulatory purposes
5. **Order Reconstruction**: Understand how large orders were executed

### Query Patterns

```bash
# Get all recent fills
GET /api/v2/spot/trade/fills

# Get fills for specific symbol
GET /api/v2/spot/trade/fills?symbol=BTCUSDT

# Get fills for specific order
GET /api/v2/spot/trade/fills?orderId=123456789

# Get fills in time range
GET /api/v2/spot/trade/fills?startTime=1690000000000&endTime=1690086400000

# Paginate through fills
GET /api/v2/spot/trade/fills?idLessThan=987654321&limit=50
```

### Best Practices

1. **Time Filtering**: Use time ranges for better performance
2. **Symbol Filtering**: Filter by trading pair when analyzing specific markets
3. **Order-Specific Queries**: Use `orderId` to get fills for specific orders
4. **Fee Tracking**: Sum up fees across all fills for total cost analysis
5. **Execution Analysis**: Use fill data to analyze order execution quality

### Example: Calculating Total Order Cost

```javascript
// Get all fills for an order
const fills = await getFills({ orderId: "123456789" });

// Calculate total executed quantity
const totalQuantity = fills.reduce((sum, fill) => 
  sum + parseFloat(fill.fillQuantity), 0);

// Calculate average execution price
const totalValue = fills.reduce((sum, fill) => 
  sum + (parseFloat(fill.fillPrice) * parseFloat(fill.fillQuantity)), 0);
const avgPrice = totalValue / totalQuantity;

// Calculate total fees
const totalFees = fills.reduce((sum, fill) => 
  sum + Math.abs(parseFloat(fill.fees)), 0);
```

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Get-Fills*
