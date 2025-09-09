# Bitget Spot Market API Documentation

## Table of Contents
1. [Get Coin Info](#get-coin-info)
2. [Get Symbol Info](#get-symbol-info)
3. [Get VIP Fee Rate](#get-vip-fee-rate)
4. [Get Ticker Information](#get-ticker-information)
5. [Get Merge Depth](#get-merge-depth)
6. [Get OrderBook Depth](#get-orderbook-depth)
7. [Get Candlestick Data](#get-candlestick-data)
8. [Get Call Auction information](#get-call-auction-information)
9. [Get History Candlestick Data](#get-history-candlestick-data)
10. [Get Recent Trades](#get-recent-trades)
11. [Get Market Trades](#get-market-trades)

---

## Get Coin Info

**Frequency limit:** 3 times/1s (IP)

### Description
Get spot coin information, supporting both individual and full queries.

### HTTP Request
`GET /api/v2/spot/public/coins`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/public/coins"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| coin      | String | No       | Coin name, If the field is left blank, all coin information will be returned by default |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695799900330,
  "data": [
    {
      "coinId": "1",
      "coin": "BTC",
      "transfer": "true",
      "chains": [
        {
          "chain": "BTC",
          "needTag": "false",
          "withdrawable": "true",
          "rechargeable": "true",
          "withdrawFee": "0.005",
          "extraWithdrawFee": "0",
          "depositConfirm": "1",
          "withdrawConfirm": "1",
          "minDepositAmount": "0.001",
          "minWithdrawAmount": "0.001",
          "browserUrl": "https://blockchair.com/bitcoin/testnet/transaction/",
          "contractAddress": "0xdac17f958d2ee523a2206206994597c13d831ec7",
          "withdrawStep": "0",
          "withdrawMinScale": "8",
          "congestion": "normal"
        }
      ]
    }
  ]
}
```

### Response Parameters
| Parameter           | Type    | Description                                                                                                                                                            |
|---------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| coinId              | String  | Currency ID                                                                                                                                                            |
| coin                | String  | Token name                                                                                                                                                             |
| transfer            | Boolean | Transferability                                                                                                                                                        |
| chains              | Array   | Support chain list                                                                                                                                                     |
| > chain             | String  | Chain name                                                                                                                                                             |
| > needTag           | Boolean | Need tag                                                                                                                                                               |
| > withdrawable      | Boolean | Withdrawal supported (The withdrawal status is subject to the official announcement)                                                                                   |
| > rechargeable      | Boolean | Deposit supported                                                                                                                                                      |
| > withdrawFee       | String  | Withdrawal transaction fee                                                                                                                                             |
| > extraWithdrawFee  | String  | Extra charge. On chain destruction: `0.1` means `10%`                                                                                                                  |
| > depositConfirm    | String  | Deposit confirmation blocks                                                                                                                                            |
| > withdrawConfirm   | String  | Withdrawal confirmation blocks                                                                                                                                         |
| > minDepositAmount  | String  | Minimum deposit amount                                                                                                                                                 |
| > minWithdrawAmount | String  | Minimum withdrawal amount                                                                                                                                              |
| > browserUrl        | String  | Blockchain explorer address                                                                                                                                            |
| > contractAddress   | String  | coin contract address                                                                                                                                                  |
| > withdrawStep      | String  | withdrawal count step If the value is not 0, it indicates that the withdrawal size should be multiple of the value. if it's 0, that means there is no the limit above. |
| > withdrawMinScale  | String  | Decimal places of withdrawal amount                                                                                                                                    |
| > congestion        | String  | chain network status `normal`: normal `congested`: congestion                                                                                                          |                                                                                                                    |
| > needTag           | Boolean | Need tag                                                                                                                                                               |
| > withdrawable      | Boolean | Withdrawal supported (The withdrawal status is subject to the official announcement)                                                                                   |
| > rechargeable      | Boolean | Deposit supported                                                                                                                                                      |
| > withdrawFee       | String  | Withdrawal transaction fee                                                                                                                                             |
| > extraWithdrawFee  | String  | Extra charge. On chain destruction: `0.1` means `10%`                                                                                                                  |
| > depositConfirm    | String  | Deposit confirmation blocks                                                                                                                                            |
| > withdrawConfirm   | String  | Withdrawal confirmation blocks                                                                                                                                         |
| > minDepositAmount  | String  | Minimum deposit amount                                                                                                                                                 |
| > minWithdrawAmount | String  | Minimum withdrawal amount                                                                                                                                              |
| > browserUrl        | String  | Blockchain explorer address                                                                                                                                            |
| > contractAddress   | String  | coin contract address                                                                                                                                                  |
| > withdrawStep      | String  | withdrawal count step If the value is not 0, it indicates that the withdrawal size should be multiple of the value. if it's 0, that means there is no the limit above. |
| > withdrawMinScale  | String  | Decimal places of withdrawal amount                                                                                                                                    |
| > congestion        | String  | chain network status `normal`: normal `congested`: congestion                                                                                                          |

---

## Get Symbol Info

**Frequency limit:** 20 times/1s (IP)

### Description
Get spot trading pair information, supporting both individual and full queries

### HTTP Request
`GET /api/v2/spot/public/symbols`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/public/symbols"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | No       | trading pair name, e.g. BTCUSDT If the field is left blank, all trading pair information will be returned by default |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1744276707885,
  "data": [
    {
      "symbol": "BTCUSDT",
      "baseCoin": "BTC",
      "quoteCoin": "USDT",
      "minTradeAmount": "0",
      "maxTradeAmount": "900000000000000000000",
      "takerFeeRate": "0.002",
      "makerFeeRate": "0.002",
      "pricePrecision": "2",
      "quantityPrecision": "6",
      "quotePrecision": "8",
      "status": "online",
      "minTradeUSDT": "1",
      "buyLimitPriceRatio": "0.05",
      "sellLimitPriceRatio": "0.05",
      "areaSymbol": "no",
      "orderQuantity": "200",
      "openTime": "1532454360000",
      "offTime": ""
    }
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| symbol | String | Trading pair |
| baseCoin | String | Base currency, e.g. "BTC" in the pair "BTCUSDT". |
| quoteCoin | String | Quoting currency, e.g. "USDT" in the trading pair "BTCUSDT". |
| minTradeAmount | String | Minimum order(obsolete) Please refer to `minTradeUSDT` |
| maxTradeAmount | String | Maximum order(obsolete) The maximum quantity is generally unlimited |
| takerFeeRate | String | Default taker transaction fee, can be overridden by individual transaction fee |
| makerFeeRate | String | Default maker transaction fee, can be overridden by individual transaction fee |
| pricePrecision | String | Pricing precision |
| quantityPrecision | String | Amount precision |
| quotePrecision | String | Quote coin precision |
| minTradeUSDT | String | Minimum trading volume (USDT) |
| status | String | Symbol status `offline`: offline `gray`: grey scale `online`: normal `halt`: suspend trading |
| buyLimitPriceRatio | String | Percentage spread between bid and ask, in decimal form E.g. 0.05 means 5% |
| sellLimitPriceRatio | String | Percentage spread between sell and current price, in decimal form E.g. 0.05 means 5% |
| orderQuantity | String | The maximum number of orders allowed for the current symbol |
| areaSymbol | String | Area symbol `yes`, `no` |
| offTime | String | Symbol off time, e.g: 1744797600000 |
| openTime | String | This field has been deprecated |

---

## Get VIP Fee Rate

**Frequency limit:** 10 times/1s (IP)

### Description
Get VIP Fee Rate

### HTTP Request
`GET /api/v2/spot/market/vip-fee-rate`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/vip-fee-rate"
```

### Request Parameters
N/A

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1675759699382,
  "data": [
    {
      "level": 1,
      "dealAmount": "1000000",
      "assetAmount": "50000",
      "takerFeeRate": "0",
      "makerFeeRate": "0",
      "btcWithdrawAmount": "300",
      "usdtWithdrawAmount": "5000000"
    }
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| level | String | VIP level |
| dealAmount | String | Total trading volume in last 30 days, USDT |
| assetAmount | String | Total assets in USDT |
| takerFeeRate | String | Taker fee. Refer to the official announcement for the real rate when 0 is shown. |
| makerFeeRate | String | Maker fee. Refer to the official announcement for the real rate when 0 is shown. |
| btcWithdrawAmount | String | 24-hour withdrawal limit in BTC |
| usdtWithdrawAmount | String | 24-hour withdrawal limit in USDT |

---

## Get Ticker Information

**Frequency limit:** 20 times/1s (IP)

### Description
Get Ticker Information, Supports both single and batch queries

### HTTP Request
`GET /api/v2/spot/market/tickers`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | No       | trading pair name, e.g. BTCUSDT If the field is left blank, all trading pair information will be returned by default |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": [
    {
      "symbol": "BTCUSDT",
      "high24h": "37775.65",
      "open": "35134.2",
      "low24h": "34413.1",
      "lastPr": "34413.1",
      "quoteVolume": "0",
      "baseVolume": "0",
      "usdtVolume": "0",
      "bidPr": "0",
      "askPr": "0",
      "bidSz": "0.0663",
      "askSz": "0.0119",
      "openUtc": "23856.72",
      "ts": "1625125755277",
      "changeUtc24h": "0.00301",
      "change24h": "0.00069"
    }
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| symbol | String | Trading pair |
| high24h | String | 24h highest price |
| open | String | 24h open price |
| lastPr | String | Latest price |
| low24h | String | 24h lowest price |
| quoteVolume | String | Trading volume in quote currency |
| baseVolume | String | Trading volume in base currency |
| usdtVolume | String | Trading volume in USDT |
| bidPr | String | Bid 1 price |
| askPr | String | Ask 1 price |
| bidSz | String | Buying 1 amount |
| askSz | String | selling 1 amount |
| openUtc | String | UTC±00:00 Entry price |
| ts | String | Current time Unix millisecond timestamp, e.g. 1690196141868 |
| changeUtc24h | String | Change at UTC+0, 0.01 means 1%. |
| change24h | String | 24-hour change, 0.01 means 1%. |

---

## Get Merge Depth

**Frequency limit:** 20 times/1s (IP)

### Description
Get Merge Depth

### HTTP Request
`GET /api/v2/spot/market/merge-depth`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/merge-depth?symbol=BTCUSDT&precision=scale0&limit=100"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair |
| precision | String | No       | Price precision, return the cumulative depth according to the selected precision as the step size, enumeration value: scale0/scale1/scale2/scale3, scale0 does not merge, the default value |
| limit     | String | No       | Fixed gear enumeration value：1/5/15/50/max，default:100，When the actual depth does not meet the limit, return according to the actual gear, and pass in max to return the maximum gear of the trading pair. |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": {
    "asks": [
      ["38084.5", "0.0039"],
      ["38085.7", "0.0018"],
      ["38086.7", "0.0310"],
      ["38088.2", "0.5303"]
    ],
    "bids": [
      ["38073.7", "0.4993000000000000"],
      ["38073.4", "0.4500"],
      ["38073.3", "0.1179"],
      ["38071.5", "0.2162"]
    ],
    "ts": "1622102974025",
    "scale": "0.1",
    "precision": "scale0",
    "isMaxPrecision": "YES"
  }
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| asks | Array | Ask depth e.g. ["38084.5","0.5"] ，"38084.5" is price，"0.5" is base coin volume |
| bids | Array | Bid depth |
| precision | String | Current gear, e.g. "scale1" |
| scale | String | Actual precision value, e.g. "0.1" |
| isMaxPrecision | String | Is max precision YES:yes NO:no |
| ts | String | Matching engine timestamp(ms), e.g. 1597026383085 |

---

## Get OrderBook Depth

**Frequency limit:** 20 times/1s (IP)

### Description
Get OrderBook Depth

### HTTP Request
`GET /api/v2/spot/market/orderbook`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=100"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair |
| type      | String | No       | Default：step0： The value enums：step0，step1，step2，step3，step4，step5 |
| limit     | String | No       | Number of queries: Default: 150, maximum: 150 |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1698303884579,
  "data": {
    "asks": [
      ["34567.15", "0.0131"],
      ["34567.25", "0.0144"]
    ],
    "bids": [
      ["34567", "0.2917"],
      ["34566.85", "0.0145"]
    ],
    "ts": "1698303884584"
  }
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| asks | Array | Ask depth e.g. ["38084.5","0.5"] ，"38084.5" is price，"0.5" is base coin volume |
| bids | Array | Bid depth |
| ts | String | Matching engine timestamp(ms), e.g. 1597026383085 |

---

## Get Candlestick Data

**Frequency limit:** 20 times/1s (IP)

### Description
Get Candlestick Data

### HTTP Request
`GET /api/v2/spot/market/candles`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/candles?symbol=BTCUSDT&granularity=1min&startTime=1659076670000&endTime=1659080270000&limit=100"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair e.g.BTCUSDT |
| granularity | String | Yes    | Time interval of charts. minute: 1min,3min,5min,15min,30min hour: 1h,4h,6h,12h day: 1day,3day week: 1week month: 1M |
| startTime | String | No       | The time start point of the chart data, Unix millisecond timestamp, e.g. 1690196141868 |
| endTime   | String | No       | The time end point of the chart data, Unix millisecond timestamp, e.g. 1690196141868 |
| limit     | String | No       | Number of queries: Default: 100, maximum: 1000. |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695800278693,
  "data": [
    ["1656604800000", "37834.5", "37849.5", "37773.5", "37773.5", "428.3462", "16198849.1079", "16198849.1079"],
    ["1656604800000", "37834.5", "37849.5", "37773.5", "37773.5", "428.3462", "16198849.1079", "16198849.1079"]
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| index[0] | String | System timestamp, Unix millisecond timestamp, e.g. 1690196141868 |
| index[1] | String | Opening price |
| index[2] | String | Highest price |
| index[3] | String | Lowest price |
| index[4] | String | Closing price |
| index[5] | String | Trading volume in base currency, e.g. "BTC" in the "BTCUSDT" pair. |
| index[6] | String | Trading volume in USDT |
| index[7] | String | Trading volume in quote currency, e.g. "USDT" in the "BTCUSDT" pair. |

---

## Get Call Auction information

**Frequency limit:** 20 times/1s (IP)

### Description
Get Call Auction information

### HTTP Request
`GET /api/v2/spot/market/auction`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/auction?symbol=BTCUSDT"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1728875148294,
  "data": {
    "stage": "stage_1",
    "stageEndTime": "1728876900000",
    "estOpeningPrice": null,
    "matchedVolume": null,
    "auctionEndTime": "1728877500000"
  }
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| stage | String | Call Auction `pre_market` pre market `stage_1` Auction 1 `stage_2` Auction 2 `stage_3` Auction 3 `success` Auction success `failure` Auction failed |
| stageEndTime | String | Current phase end time, milliseconds |
| estOpeningPrice | String | Estimated Opening Price |
| matchedVolume | String | Matched Volume, base coin |
| auctionEndTime | String | Call Auction end time, milliseconds |

---

## Get History Candlestick Data

**Frequency limit:** 20 times/1s (IP)

### Description
Get History Candlestick Data

### HTTP Request
`GET /api/v2/spot/market/history-candles`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/history-candles?symbol=BTCUSDT&granularity=1min&endTime=1659080270000&limit=100"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair |
| granularity | String | Yes    | Time interval of charts. minute: 1min,3min,5min,15min,30min hour: 1h,4h,6h,12h day: 1day,3day week: 1week month: 1M |
| endTime   | String | Yes      | The time end point of the chart data, Unix millisecond timestamp, e.g. 1690196141868 |
| limit     | String | No       | Number of queries: Default: 100, maximum: 200. |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695799900330,
  "data": [
    ["1646064000000", "43500.8", "48207.2", "38516", "46451.9", "2581.4668", "118062073.82644", "118062073.82644"],
    ["1648742400000", "46451.9", "55199.6", "15522.1", "38892.5", "42331329.5473", "1726993402150.991724", "1726993402150.991724"]
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| index[0] | String | System timestamp, Unix millisecond timestamp, e.g. 1690196141868 |
| index[1] | String | Opening price |
| index[2] | String | Highest price |
| index[3] | String | Lowest price |
| index[4] | String | Closing price |
| index[5] | String | Trading volume in base currency, e.g. "BTC" in the "BTCUSDT" pair. |
| index[6] | String | Trading volume in USDT |
| index[7] | String | Trading volume in quote currency, e.g. "USDT" in the "BTCUSDT" pair. |

---

## Get Recent Trades

**Frequency limit:** 10 times/1s (IP)

### Description
Get Recent Trades

### HTTP Request
`GET /api/v2/spot/market/fills`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/fills?symbol=BTCUSDT&limit=100"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair name, e.g. BTCUSDT |
| limit     | String | No       | Default: 100, maximum: 500 |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1695808949356,
  "data": [
    {
      "symbol": "BFTUSDT",
      "tradeId": "1",
      "side": "buy",
      "price": "2.38735",
      "size": "2470.6224",
      "ts": "1622097282536"
    },
    {
      "symbol": "BFTUSDT",
      "tradeId": "2",
      "side": "sell",
      "price": "2.38649",
      "size": "3239.7976",
      "ts": "1622097280642"
    }
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| symbol | String | Trading pair |
| tradeId | String | Order ID Descending |
| side | String | Direction Buy Sell |
| price | String | Order price |
| size | String | Filled quantity |
| ts | String | Transaction time, Unix millisecond timestamp, e.g. 1690196141868 |

---

## Get Market Trades

**Rate limit:** 10 req/sec/IP

### Description
Get Market Trades

**Notes:**
- The time interval between startTime and endTime should not exceed 7 days.
- It supports to get the data within 90days. You can download the older data on Bitget [web](https://www.bitget.com/data-download).

### HTTP Request
`GET /api/v2/spot/market/fills-history`

### Request Example
```bash
curl "https://api.bitget.com/api/v2/spot/market/fills-history?symbol=BTCUSDT&limit=20&startTime=1678965010861&endTime=1678965910861"
```

### Request Parameters
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| symbol    | String | Yes      | Trading pair name, e.g. BTCUSDT |
| limit     | String | No       | number of data returned. Default: 500, maximum: 1000 |
| idLessThan | String | No      | Order ID, returns records less than the specified 'tradeId'. |
| startTime | String | No       | startTime, Unix millisecond timestamp e.g. 1690196141868 startTime and endTime should be within 7days. |
| endTime   | String | No       | endTime, Unix millisecond timestamp e.g. 1690196141868 startTime and endTime should be within 7days. |

### Response Example
```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1744275754521,
  "data": [
    {
      "symbol": "ETHUSDT",
      "tradeId": "1294151170843025500",
      "side": "Buy",
      "price": "1592.58",
      "size": "2.1982",
      "ts": "1744275603000"
    },
    {
      "symbol": "ETHUSDT",
      "tradeId": "1294151170834636801",
      "side": "Sell",
      "price": "1592.57",
      "size": "0.0045",
      "ts": "1744275603000"
    }
  ]
}
```

### Response Parameters
| Parameter | Type | Description |
|-----------|------|--------------|
| symbol | String | Trading pair |
| tradeId | String | Order ID Descending |
| side | String | Direction `Buy` `Sell` |
| price | String | Order price |
| size | String | Filled quantity |
| ts | String | Transaction time(second level) Unix millisecond timestamp, e.g. 1744275603000 |

---

## API Base URL
**Base URL:** `https://api.bitget.com`

## Authentication
These are all public endpoints and do not require authentication.

## Error Codes
All successful responses will have `"code": "00000"`. Please refer to the [Error Code documentation](https://www.bitget.com/api-doc/spot/error) for detailed error handling.

---

*Documentation generated from Bitget API official documentation. Last updated: September 2025*
