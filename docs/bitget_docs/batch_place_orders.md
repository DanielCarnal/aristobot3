# Batch Place Orders - Bitget Spot Trading API

**Rate limit:** 5 requests/second/UID  
**Trader rate limit:** 1 request/second/UID

## Description

Place Orders in Batch

## HTTP Request

**POST** `/api/v2/spot/trade/batch-orders`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/batch-orders" \
-H "ACCESS-KEY:*******" \
-H "ACCESS-SIGN:*" \
-H "ACCESS-PASSPHRASE:*" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json" \
-d '{
  "symbol":"BTCUSDT",
  "orderList":[
    {
      "side":"buy",
      "orderType":"limit",
      "force":"gtc",
      "price":"23222.5",
      "size":"1",
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
| `orderList` | Array | Yes | Collection of placing orders, **maximum length: 50** |

### orderList Array Elements

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | No | Trading pair name, e.g. BTCUSDT |
| `side` | String | Yes | Order Direction<br>• `buy`: Buy<br>• `sell`: Sell |
| `orderType` | String | Yes | Order type<br>• `limit`: Limit order<br>• `market`: Market order |
| `force` | String | Yes | Execution strategy (invalid when orderType is market)<br>• `gtc`: Normal limit order, good till cancelled<br>• `post_only`: Post only<br>• `fok`: Fill or kill<br>• `ioc`: Immediate or cancel |
| `price` | String | No | Limit price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `size` | String | Yes | Amount<br>• For **Limit and Market-Sell** orders, it represents the number of **base coins**<br>• For **Market-Buy** orders, it represents the number of **quote coins**<br>The decimal places of amount can be got through [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `clientOid` | String | No | Custom order ID |
| `stpMode` | String | No | STP Mode, default `none`<br>• `none`: not setting STP<br>• `cancel_taker`: cancel taker order<br>• `cancel_maker`: cancel maker order<br>• `cancel_both`: cancel both of taker and maker orders |
| `presetTakeProfitPrice` | String | No | Take profit price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `executeTakeProfitPrice` | String | No | Take profit execute price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `presetStopLossPrice` | String | No | Stop loss price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `executeStopLossPrice` | String | No | Stop loss execute price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1666336231317,
  "data": {
    "successList": [
      {
        "orderId": "121211212122",
        "clientOid": "1"
      }
    ],
    "failureList": [
      {
        "orderId": "121211212122",
        "clientOid": "1",
        "errorMsg": "clientOrderId duplicate"
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
   - All orders in the batch use the same trading pair specified in the main `symbol` parameter
   - Individual `symbol` fields in orderList are ignored
   - Suitable for bulk orders on one trading pair

2. **Cross-Currency Mode (`batchMode=multiple`)**:
   - Each order can have a different trading pair
   - The `symbol` field in each order is required
   - Main `symbol` parameter is ignored
   - Suitable for placing orders across multiple trading pairs

### Batch Processing

- **Maximum 50 orders** can be processed in a single request
- Each order is processed independently
- Some orders may succeed while others fail
- Check both `successList` and `failureList` in the response

### Order Types and Parameters

1. **Limit Orders**: Require `price` parameter
2. **Market Orders**: Do not require `price` parameter, `force` parameter is invalid

### Amount Calculation (Per Order)

- **Limit orders & Market Sell**: `size` = amount of base currency
- **Market Buy**: `size` = amount of quote currency

### Self Trade Prevention (STP)

Use `stpMode` to prevent orders from trading against each other within the same account.

### Rate Limits

- **Standard users**: 5 requests per second per UID
- **Copy trading traders**: 1 request per second per UID

### Use Cases

1. **Grid Trading**: Place multiple limit orders at different price levels
2. **Portfolio Entry**: Place orders across multiple trading pairs
3. **DCA Strategy**: Place multiple buy orders at different prices
4. **Liquidity Provision**: Place both buy and sell orders

### Best Practices

1. **Check Both Lists**: Always examine both `successList` and `failureList`
2. **Handle Partial Failures**: Implement retry logic for failed orders
3. **Validate Before Sending**: Ensure all parameters are correct to minimize failures
4. **Stay Within Limits**: Don't exceed 50 orders per request
5. **Monitor Rate Limits**: Respect the rate limits based on your account type

### Common Error Scenarios

- Insufficient balance
- Invalid trading pair
- Duplicate `clientOid`
- Price/size precision errors
- Market conditions (e.g., price limits)

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Batch-Place-Orders*
