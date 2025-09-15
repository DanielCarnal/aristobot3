# Get History Orders - Bitget Spot Trading API

**Frequency limit:** 20 times/1s (UID)

## Description

Get History Orders (It only supports to get the data within 90days. The older data can be downloaded from web)

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
| `startTime` | String | No | The record start time for the query. Unix millisecond timestamp, e.g. 1690196141868. (For Managed Sub-Account, the StartTime cannot be earlier than the binding time) |
| `endTime` | String | No | The end time of the record for the query. Unix millisecond timestamp, e.g. 1690196141868 |
| `idLessThan` | String | No | Requests the content on the page before this ID (older data), the value input should be the orderId of the corresponding interface. |
| `limit` | String | No | Limit number default 100 max 100 |
| `orderId` | String | No | OrderId |
| `tpslType` | String | No | Order type default `normal`<br>• `normal`: spot order<br>• `tpsl`: spot tpsl order |
| `requestTime` | String | No | Request Time Unix millisecond timestamp |
| `receiveWindow` | String | No | Valid window period Unix millisecond timestamp |

## Response Example

```json
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695808949356,
    "data": [
        {
            "userId": "*********",
            "symbol": "ETHUSDT",
            "orderId": "*****************************",
            "clientOid": "*****************************",
            "price": "0",
            "size": "20.0000000000000000",
            "orderType": "market",
            "side": "buy",
            "status": "filled",
            "priceAvg": "1598.1000000000000000",
            "baseVolume": "0.0125000000000000",
            "quoteVolume": "19.9762500000000000",
            "enterPointSource": "WEB",
            "feeDetail": "{\"newFees\":{\"c\":0,\"d\":0,\"deduction\":false,\"r\":-0.112079256,\"t\":-0.112079256,\"totalDeductionFee\":0},\"USDT\":{\"deduction\":false,\"feeCoinCode\":\"ETH\",\"totalDeductionFee\":0,\"totalFee\":-0.1120792560000000}}",
            "orderSource": "market",
            "cTime": "1698736299656",
            "uTime": "1698736300363",
            "tpslType": "normal",
            "cancelReason": "",
            "triggerPrice": null
        }
    ]
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `userId` | String | User id |
| `symbol` | String | Trading pair name |
| `orderId` | String | Order ID |
| `clientOid` | String | Client Order ID |
| `price` | String | Order price |
| `size` | String | Amount (orderType = limit means base coin; orderType = market means quote coin) |
| `orderType` | String | Order type<br>• `limit`: Limit price<br>• `market`: Market price |
| `side` | String | Direction |
| `status` | String | Order status<br>• `live`: unfilled<br>• `partially_filled`: partially filled<br>• `filled`: filled<br>• `cancelled`: cancelled |
| `priceAvg` | String | Average fill price |
| `baseVolume` | String | Filled volume (base coin) |
| `quoteVolume` | String | Filled volume (quote coin) |
| `enterPointSource` | String | Client<br>• `WEB`: WEB Client<br>• `APP`: APP Client<br>• `API`: API Client<br>• `SYS`: SYS Client<br>• `ANDROID`: ANDROID Client<br>• `IOS`: IOS Client |
| `orderSource` | String | Order source<br>• `normal`: Normal order<br>• `market`: Market order<br>• `spot_trader_buy`: Elite spot trade to buy (elite traders)<br>• `spot_follower_buy`: Copy trade to buy (followers)<br>• `spot_trader_sell`: Elite spot trade to sell (elite traders)<br>• `spot_follower_sell`: Copy trade to sell (followers) |
| `cTime` | String | Creation time, Unix millisecond timestamp, e.g. 1690196141868 |
| `uTime` | String | Update time, Unix millisecond timestamp, e.g. 1690196141868 |
| `feeDetail` | String | Fee details. If there is a "newFees" field, then "newFees" represents the fee details. If not, the remaining information is the fee details. |
| `triggerPrice` | String | Spot tpsl trigger price |
| `tpslType` | String | • `normal`: spot order<br>• `tpsl`: spot tpsl order |
| `cancelReason` | String | Cancel reason<br>• `normal_cancel`: Normal cancel<br>• `stp_cancel`: Cancelled by STP |

### Fee Details Structure

#### newFees (New Fee Structure)
| Parameter | Type | Description |
|-----------|------|-------------|
| `c` | String | Amount deducted by coupons, unit: currency obtained from the transaction |
| `d` | String | Amount deducted in BGB (Bitget Coin), unit: BGB |
| `r` | String | If the BGB balance is insufficient to cover the fees, the remaining amount is deducted from the currency obtained from the transaction |
| `t` | String | The total fee amount to be paid, unit: currency obtained from the transaction |
| `deduction` | String | Ignore |
| `totalDeductionFee` | String | Ignore |

#### Legacy Fee Structure (if no "newFees" field)
| Parameter | Type | Description |
|-----------|------|-------------|
| `{Currency}` | String | Currency used for fee deduction (not fixed; if BGB deduction is enabled, it's BGB, otherwise, it's the currency obtained from the transaction) |
| `deduction` | String | Whether there is a fee deduction |
| `feeCoinCode` | String | Transaction fee coin code |
| `totalDeductionFee` | String | Deduction amount unit: BGB |
| `totalFee` | String | The total fee amount to be paid, unit: currency obtained from the transaction |

## Important Notes

### Query Scope

- Returns **filled and cancelled orders only**
- **Data availability**: Only supports data within 90 days
- **Older data**: Can be downloaded from web interface
- Use **Get Current Orders** for active orders (`live`, `partially_filled`)

### Time Range

- **Maximum time range**: 90 days
- **Default behavior**: Returns recent history if no time range specified
- **Managed Sub-Account**: StartTime cannot be earlier than the binding time
- **Recommended**: Use reasonable time windows for better performance

### Pagination

- **Default limit**: 100 orders
- **Maximum limit**: 100 orders per request
- Use `idLessThan` for pagination to get older orders (input should be orderId)

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
6. **Fee Detail Parsing**: Check for "newFees" field first before parsing legacy structure

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Get-History-Orders*
