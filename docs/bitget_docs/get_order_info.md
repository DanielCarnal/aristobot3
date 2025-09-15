# Get Order Info - Bitget Spot Trading API

**Frequency limit:** 20 times/1s (UID)

## Description

Get Order Info

## HTTP Request

**GET** `/api/v2/spot/trade/orderInfo`

### Request Example

```bash
curl "https://api.bitget.com/api/v2/spot/trade/orderInfo?orderId=1234567890" \
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
| `orderId` | String | No | Order ID. Either `orderId` or `clientOid` is required |
| `clientOid` | String | No | Client customized ID. Either `clientOid` or `orderId` is required |
| `requestTime` | String | No | Request Time, Unix millisecond timestamp |
| `receiveWindow` | String | No | Valid window period, Unix millisecond timestamp |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695865476577,
  "data": [
    {
      "userId": "**********",
      "symbol": "BTCUSDT",
      "orderId": "121211212122",
      "clientOid": "121211212122",
      "price": "0",
      "size": "10.0000000000000000",
      "orderType": "market",
      "side": "buy",
      "status": "filled",
      "priceAvg": "13000.0000000000000000",
      "baseVolume": "0.0007000000000000",
      "quoteVolume": "9.1000000000000000",
      "enterPointSource": "API",
      "feeDetail": "{\"BGB\":{\"deduction\":true,\"feeCoinCode\":\"BGB\",\"totalDeductionFee\":-0.0041,\"totalFee\":-0.0041},\"newFees\":{\"c\":0,\"d\":0,\"deduction\":false,\"r\":-0.112079256,\"t\":-0.112079256,\"totalDeductionFee\":0}}",
      "orderSource": "market",
      "cancelReason": "",
      "cTime": "1695865232127",
      "uTime": "1695865233051"
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
| `clientOid` | String | Customized ID |
| `price` | String | Order price |
| `size` | String | Amount. Limit represents the number of base coins. Market-buy represents the number of quote coins. Market-sell represents the number of base coins |
| `orderType` | String | Order type<br>• `limit`: Limit price<br>• `market`: Market price |
| `side` | String | Direction (buy/sell) |
| `status` | String | Order status<br>• `live`: pending match<br>• `partially_filled`: Partially filled<br>• `filled`: All filled<br>• `cancelled`: The order is cancelled |
| `priceAvg` | String | Filled price |
| `baseVolume` | String | Filled quantity (base coin) |
| `quoteVolume` | String | Total trading amount (quote coin) |
| `enterPointSource` | String | Client source<br>• `WEB`: Web Client<br>• `APP`: App Client<br>• `API`: API Client<br>• `SYS`: System Client<br>• `ANDROID`: Android Client<br>• `IOS`: iOS Client |
| `cTime` | String | Creation time, Unix millisecond timestamp, e.g. 1690196141868 |
| `uTime` | String | Update time, Unix millisecond timestamp, e.g. 1690196141868 |
| `orderSource` | String | Order source<br>• `normal`: Normal order<br>• `market`: Market order<br>• `spot_trader_buy`: Elite spot trade to buy (elite traders)<br>• `spot_follower_buy`: Copy trade to buy (followers)<br>• `spot_trader_sell`: Elite spot trade to sell (elite traders)<br>• `spot_follower_sell`: Copy trade to sell (followers) |
| `feeDetail` | String | Transaction fee breakdown (JSON string) |
| `cancelReason` | String | Cancel reason<br>• `normal_cancel`: Normal cancel<br>• `stp_cancel`: Cancelled by STP |

### Fee Detail Structure

The `feeDetail` field contains a JSON string with fee information:

#### New Fee Structure (`newFees`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `c` | String | Amount deducted by coupons, unit: currency obtained from the transaction |
| `d` | String | Amount deducted in BGB (Bitget Coin), unit: BGB |
| `r` | String | If the BGB balance is insufficient to cover the fees, the remaining amount is deducted from the currency obtained from the transaction |
| `t` | String | The total fee amount to be paid, unit: currency obtained from the transaction |
| `deduction` | String | Ignore |
| `totalDeductionFee` | String | Ignore |

#### Legacy Fee Structure (e.g., `BGB`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `deduction` | String | Whether there is a fee deduction |
| `feeCoinCode` | String | Transaction fee coin code |
| `totalDeductionFee` | String | Deduction amount unit: BGB |
| `totalFee` | String | The total fee amount to be paid, unit: currency obtained from the transaction |

## Important Notes

### Order Identification

- **Either `orderId` or `clientOid` is required** to identify the order
- Use `orderId` for system-generated order IDs
- Use `clientOid` for your custom order IDs

### Order Status Values

1. **`live`**: Order is pending match (open and waiting)
2. **`partially_filled`**: Order is partially executed
3. **`filled`**: Order is completely executed
4. **`cancelled`**: Order has been cancelled

### Amount Fields Understanding

- **`size`**: Original order amount
  - For limit orders: amount in base currency
  - For market buy: amount in quote currency
  - For market sell: amount in base currency
- **`baseVolume`**: Actual filled amount in base currency
- **`quoteVolume`**: Actual filled amount in quote currency

### Price Fields

- **`price`**: Original order price (0 for market orders)
- **`priceAvg`**: Average execution price

### Time Fields

- **`cTime`**: When the order was created
- **`uTime`**: When the order was last updated

### Rate Limits

- **20 times per second per UID** (Frequency limit: 20 times/1s)

### Use Cases

1. **Order Tracking**: Monitor specific order status and execution
2. **Trade Reconciliation**: Verify order execution details
3. **Fee Analysis**: Understand fee breakdown and deductions
4. **Audit Trail**: Track order lifecycle for compliance
5. **Performance Analysis**: Calculate execution quality metrics

### Best Practices

1. **Use Appropriate Identifier**: Use `orderId` for system IDs, `clientOid` for custom IDs
2. **Handle All Status Types**: Implement logic for all possible order statuses
3. **Parse Fee Details**: Parse the JSON string in `feeDetail` for accurate fee calculation
4. **Monitor Rate Limits**: Stay within the 20 requests/second limit
5. **Error Handling**: Handle cases where order is not found

### Common Use Patterns

```javascript
// Check if order is still active
if (status === 'live' || status === 'partially_filled') {
  // Order can still be modified/cancelled
}

// Calculate fill percentage
const fillPercentage = (parseFloat(baseVolume) / parseFloat(size)) * 100;

// Parse fee details
const fees = JSON.parse(feeDetail);
```

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Get-Order-Info*
