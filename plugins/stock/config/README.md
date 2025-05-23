# 股票数据插件

## 功能描述

股票数据插件用于获取A股市场的实时行情、历史数据、个股详情、财报信息等多种股票相关数据，帮助用户快速了解股市动态。

## 使用方法

在群聊中发送以下命令：

- `股票 历史 [股票代码]` - 获取股票历史K线数据
  - 例如：`股票 历史 600519` - 获取贵州茅台历史数据
  - 高级用法：`股票 历史 600519 daily 20230101 20231231 qfq` - 指定周期、起止日期和复权方式

- `股票 实时 [股票代码]` - 获取股票实时行情数据
  - 例如：`股票 实时 000001` - 获取平安银行最新行情

- `股票 新闻 [股票代码]` - 获取股票相关新闻
  - 例如：`股票 新闻 000858` - 获取五粮液相关新闻

- `股票 个股 [股票代码]` - 获取股票详细信息及买卖盘
  - 例如：`股票 个股 600030` - 获取中信证券详细信息

- `股票 总貌` - 获取沪深两市总体行情概览

- `股票 财报` - 获取今日财报发布信息

- `股票 预测 [股票代码]` - 获取股票AI预测分析（待实现）

## 配置文件

本插件的主要配置文件为`config.toml`，包含API配置和权限控制。

### 配置项说明

```toml
# 股票数据API配置
[api]
provider = "your_api_provider" #  例如： sina, tushare
api_key = "your_api_key_here"

# 白名单配置
[whitelist]
# 允许使用股票插件的群组ID列表
group_ids = [123456789]
# 允许使用股票插件的用户ID列表
user_ids = [987654321]
```

## 使用方法

1. 将`config.example.toml`复制为`config.toml`
2. 修改`config.toml`中的白名单配置，添加允许使用此插件的群组ID和用户ID
3. 可选：配置API提供商和密钥（目前使用akshare库，无需API密钥）

## 数据来源

本插件主要使用[akshare](https://akshare.xyz/)金融数据接口包获取A股市场数据，包括：

- A股历史行情数据
- 实时市场行情
- 股票基本信息
- 个股新闻资讯
- 财务报表信息
- 市场概览数据

## 注意事项

- 本插件提供的数据仅供参考，不构成任何投资建议
- 请合理控制查询频率，避免对服务器造成过大压力
- 数据可能存在延迟，交易决策请以专业交易软件为准
- 历史数据图表和表格会暂时保存在`plugins/stock/data`目录下

## 常见问题

- 如果无法获取数据，可能是网络问题或数据源暂时不可用
- 某些股票代码可能因数据源限制无法查询，请尝试其他股票
- 如需查询指数，请确保输入正确的指数代码 