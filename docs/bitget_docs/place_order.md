# Place Order - Bitget Spot Trading API

**Rate limit:** 10 requests/second/UID  
**Rate limit:** 1 request/second/UID for **copy trading traders**

## Description

- For elite traders, please strictly adhere to the list of trading pairs specified in the [Available trading pairs and parameters for elite traders](https://www.bitget.com/zh-CN/support/articles/12560603808895) when placing orders using the Copy Trading API Key. Trading pairs outside the announced list are not available for copy trading.

## HTTP Request

**POST** `/api/v2/spot/trade/place-order`

### Request Example

```bash
curl -X POST "https://api.bitget.com/api/v2/spot/trade/place-order" \
-H "ACCESS-KEY:your apiKey" \
-H "ACCESS-SIGN:*******" \
-H "ACCESS-PASSPHRASE:*****" \
-H "ACCESS-TIMESTAMP:1659076670000" \
-H "locale:en-US" \
-H "Content-Type: application/json" \
-d '{
  "symbol": "BTCUSDT",
  "side": "buy",
  "orderType": "limit",
  "force":"gtc",
  "price":"23222.5",
  "size":"1",
  "clientOid":"121211212122"
}'
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | String | Yes | Trading pair name, e.g. BTCUSDT. All symbols can be returned by [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `side` | String | Yes | Order Direction<br>• `buy`: Buy<br>• `sell`: Sell |
| `orderType` | String | Yes | Order type<br>• `limit`: Limit order<br>• `market`: Market order |
| `force` | String | Yes | Execution strategy (It is invalid when orderType is market)<br>• `gtc`: Normal limit order, good till cancelled<br>• `post_only`: Post only<br>• `fok`: Fill or kill<br>• `ioc`: Immediate or cancel |
| `price` | String | No | Limit price. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `size` | String | Yes | Amount<br>• For **Limit and Market-Sell** orders, it represents the number of **base coins**<br>• For **Market-Buy** orders, it represents the number of **quote coins**<br>The decimal places of amount can be got through [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `clientOid` | String | No | Custom order ID. It's invalid when `tpslType` is `tpsl` |
| `triggerPrice` | String | No | SPOT TP/SL trigger price, only required in SPOT TP/SL order |
| `tpslType` | String | No | Order type<br>• `normal`: SPOT order (default)<br>• `tpsl`: SPOT TP/SL order |
| `requestTime` | String | No | Request Time, Unix millisecond timestamp |
| `receiveWindow` | String | No | Valid time window, Unix millisecond timestamp. If it's set, the request is valid only when the time range between the timestamp in the request and the time that server received the request is within `receiveWindow` |
| `stpMode` | String | No | STP Mode (Self Trade Prevention)<br>• `none`: not setting STP (default)<br>• `cancel_taker`: cancel taker order<br>• `cancel_maker`: cancel maker order<br>• `cancel_both`: cancel both of taker and maker orders |
| `presetTakeProfitPrice` | String | No | Take profit price. It's invalid when `tpslType` is `tpsl`. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `executeTakeProfitPrice` | String | No | Take profit execute price. It's invalid when `tpslType` is `tpsl`. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `presetStopLossPrice` | String | No | Stop loss price. It's invalid when `tpslType` is `tpsl`. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |
| `executeStopLossPrice` | String | No | Stop loss execute price. It's invalid when `tpslType` is `tpsl`. The decimal places of price and the price step can be returned by the [Get Symbol Info](https://www.bitget.com/api-doc/spot/market/Get-Symbols) interface |

## Response Example

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": {
    "orderId": "1001",
    "clientOid": "121211212122"
  }
}
```

## Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `orderId` | String | Order ID |
| `clientOid` | String | Custom order ID |

## Important Notes

### Order Types and Parameters

1. **Limit Orders**: Require `price` parameter
2. **Market Orders**: Do not require `price` parameter, `force` parameter is invalid
3. **TP/SL Orders**: Use `tpslType=tpsl` and `triggerPrice`

### Amount Calculation

- **Limit orders & Market Sell**: `size` = amount of base currency (e.g., BTC in BTCUSDT)
- **Market Buy**: `size` = amount of quote currency (e.g., USDT in BTCUSDT)

### Execution Strategies (`force` parameter)

- **GTC (Good Till Cancel)**: Order remains active until filled or cancelled
- **Post Only**: Order will only be filled as a maker order (provides liquidity)
- **FOK (Fill or Kill)**: Order must be filled immediately and completely or cancelled
- **IOC (Immediate or Cancel)**: Fill immediately, cancel any unfilled portion

### Self Trade Prevention (STP)

Use `stpMode` to prevent your orders from trading against each other:
- `cancel_taker`: Cancel the incoming (taker) order
- `cancel_maker`: Cancel the existing (maker) order  
- `cancel_both`: Cancel both orders

### Rate Limits

- **Standard trading**: 10 requests per second per UID
- **Copy trading traders**: 1 request per second per UID

---

*Documentation extracted from: https://www.bitget.com/api-doc/spot/trade/Place-Order*
