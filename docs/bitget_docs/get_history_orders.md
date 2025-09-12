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


## Response Parameter
Parameter	Type	Description
userId	String	User id
symbol	String	Trading pair name
orderId	String	Order ID
clientOid	String	Client Order ID
price	String	Order price
size	String	Amount
(orderType = limit means base coin; orderType = market means quote coin)
orderType	String	Order type
limit Limit price
market Market price
side	String	Direction
status	String	Order status
live:unfilled;
partially_filled:partially filled;
filled:filled;
cancelled:cancelled;
priceAvg	String	Average fill price
baseVolume	String	Filled volume (base coin)
quoteVolume	String	Filled volume (quote coin)
enterPointSource	String	Client
WEB WEB Client
APP APP Client
API API Client
SYS SYS Client
ANDROID ANDROID Client
IOS IOS Client
orderSource	String	Order source
normal Normal order
market Market order
spot_trader_buy Elite spot trade to buy (elite traders)
spot_follower_buy Copy trade to buy (followers)
spot_trader_sell Elite spot trade to sell (elite traders)
spot_follower_sell Copy trade to sell (followers)
cTime	String	Creation time, Unix millisecond timestamp, e.g. 1690196141868
uTime	String	Update time, Unix millisecond timestamp, e.g. 1690196141868
feeDetail	String	Fee details. If there is a "newFees" field, then "newFees" represents the fee details. If not, the remaining information is the fee details.
> newFees	String	Fee details for "newFees".
>> c	String	Amount deducted by coupons, unit：currency obtained from the transaction.
>> d	String	Amount deducted in BGB (Bitget Coin), unit：BGB
>> r	String	If the BGB balance is insufficient to cover the fees, the remaining amount is deducted from the currency obtained from the transaction.
>> t	String	The total fee amount to be paid, unit ：currency obtained from the transaction.
>> deduction	String	Ignore.
>> totalDeductionFee	String	Ignore.
> BGB	String	If there is no "newFees" field, this data represents earlier historical data. This key represents the currency used for fee deduction (it is not fixed; if BGB deduction is enabled, it's BGB, otherwise, it's the currency obtained from the transaction).
>> deduction	String	Whether there is a fee deduction.
>> feeCoinCode	String	Transaction fee coin code
>> totalDeductionFee	String	Deduction amount unit： BGB
>> totalFee	String	The total fee amount to be paid, unit：currency obtained from the transaction.
triggerPrice	String	spot tpsl trigger price
tpslType	String	normal spot order
tpsl spot tpsl order
cancelReason	String	Cancel reason
normal_cancel: Normal cancel
stp_cancel: Cancelled by STP
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
