# 电商领域入门手册（面向 Agent 工程师）

> 目的：让你在 1–2 周内建立"能跟电商业务方对话、能为售后 Agent 做正确取舍"的领域知识。
> 读者：有工程背景、但没做过电商的你。
> 用法：先通读一遍建立地图；做项目时按章回查；面试前用第 10 章的 30 个问题自测。
>
> 诚实声明：本文中的数字是"行业常见区间"，用于建立量级直觉，不是精确统计；引用时请以你自己核实的数据为准。

---

## 目录

1. 价值链与"钱在哪里"
2. 客服与售后经济学
3. KPI 手册
4. 业务规则大全（退货 / 退款 / 换货 / 保修）
5. 系统地图与数据流
6. 退货状态机（Shopify 真实版）
7. 数据模型（Shopify 真实 schema）
8. 真实政策语料：结构化、版本化、冲突设计
9. 售后 Agent 的常见失败模式
10. 术语表 + 30 个面试问题

---

## 1. 价值链与"钱在哪里"

电商的价值链可以粗分为 6 段。对每一段，你要能回答三个问题：**客户在问什么、痛点在哪、谁为它买单。**

| 环节 | 客户的真实问题 | 主要指标 | 成本/收益 | Agent 是否合适 |
|---|---|---|---|---|
| **发现 Discovery** | "有没有适合我的 X？" | 搜索相关性、转化率 | 相关性 ↑ → GMV ↑ | 适合（检索/排序） |
| **考虑 Consideration** | "A 和 B 哪个好？" | 加购率、跳出率 | 降低决策成本 | 适合（比较/推荐） |
| **购买 Purchase** | 结账、支付 | 转化率、弃单率 | 高风险 | **不适合自动执行** |
| **履约 Fulfillment** | "我的货到哪了？"（WISMO） | 送达准时率、WISMO 率 | **高频、低歧义、成本高** | **非常适合** |
| **售后 Post-purchase** | 退货、换货、退款、保修 | 退款成本、退货率、政策合规 | **直接烧钱、决策重** | **非常适合（本项目的核心）** |
| **留存 Retention** | 复购、会员、积分 | 复购率、LTV | 长期价值 | 适合（但不紧急） |

**核心结论**：真正高频、高成本、且**可被 agent 安全消化**的两块是 **WISMO** 和 **售后（退货/退款）**。这也是本项目选它们的原因。

**为什么购买环节不交给 agent**：支付不可逆、欺诈风险高、合规要求严。行业共识是"结账只渲染、不扣款"——模型提议，harness 处置。

---

## 2. 客服与售后经济学

### 2.1 WISMO：最大的一块

**WISMO = "Where Is My Order"（我的订单到哪了）。**

- 占 DTC（Direct-to-Consumer，直面消费者）品牌客服量的 **30%–50%**。
- 单次人工处理成本 **约 $4–$15**（取决于渠道：自助 < 在线聊天 < 邮件 < 电话）。
- 它是**最容易自动化**的一类：答案确定、数据在系统里、几乎不需要判断。

**为什么它这么贵**：每一次查询都要客服打开 OMS 查订单、看物流、解释延迟、安抚客户。重复且可预测。

**自动化的价值**：把 WISMO 的**自助解决率（deflection）**从 0 提到 60%–80%，直接省下这部分人力。

### 2.2 退货/退款：最烧钱的一块

- 线上零售退货率因品类差异极大（服装可到 20%–40%，电子产品低得多）。
- 退货相关的**客服接触**（"怎么退""什么时候到账""能不能换"）是第二大客服来源。
- 退货本身有成本：逆向物流、检验、重新上架/报废、**退款金额**。
- 更关键：**错误批准 = 直接损失**；**错误拒绝 = 客户流失 + 差评**。

所以售后 Agent 的价值不是"省客服工资"，而是**在政策合规的前提下，把可标准化的决策自动化，同时把有风险的决策升级给人工**。

### 2.3 一个简单的 ROI 心算

```
年节省 ≈ WISMO 量 × 单次成本 × 自动化率
      + 退货咨询量 × 单次成本 × 自动化率
      − 误判造成的退款损失 − 系统成本
```

面试时能这样算，比说"提升效率"强得多。

---

## 3. KPI 手册

每个指标你要能说出：**定义、公式、为什么重要、怎么用它评估 agent。**

| 指标 | 定义 / 公式 | 行业常见区间 | 对 Agent 的意义 |
|---|---|---|---|
| **WISMO rate** | WISMO 工单数 / 总工单数 | 30%–50% | 你的自动化天花板 |
| **Deflection rate**（containment） | 无需人工的会话数 / 总会话数 | 目标是 40%–70% | **核心 ROI 指标** |
| **FCR**（First Contact Resolution） | 一次接触解决的会话数 / 总会话数 | 70%–85% | 质量指标：别把问题推来推去 |
| **Cost per contact** | 总客服成本 / 接触数 | $4–$15 | 省钱数字 |
| **CSAT** | 满意度评分（1–5 或 %） | 80%+ 为好 | 别为了省钱惹怒客户 |
| **AHT**（Average Handle Time） | 总处理时长 / 会话数 | 因渠道而异 | 自动化要降低它 |
| **Return contact rate** | 退货相关接触 / 订单数 | 因品类而异 | 你的主战场 |
| **Refund cycle time** | 从申请到退款到账的时长 | 越短越好 | 客户最在意 |
| **EDD accuracy**（Estimated Delivery Date） | 准时送达订单 / 总订单 | 越高 WISMO 越少 | WISMO 的根因指标 |
| **Escalation rate** | 升级到人工的比例 | 越低越好，但**安全 > 低** | 你的护栏有效性 |

**关键取舍**：deflection 高不一定好。**"把客户挡在门外"（假 deflection）比不自动化更糟**。所以要看 **FCR + CSAT + escalation precision** 一起。

---

## 4. 业务规则大全（退货 / 退款 / 换货 / 保修）

这一章是"决策"的核心。你要能背出这些规则，并知道它们如何组合。

### 4.1 退货资格（Return Eligibility）

一个退货请求能否被批准，通常同时取决于：

1. **退货窗口（return window）**：如"签收后 30 天内"。
   - **起算日**是关键歧义：签收日 vs 发货日 vs 下单日。政策必须明确。
2. **商品状态**：未使用、吊牌完整、原包装。
3. **不可退品类**：final sale（清仓）、礼品卡、内衣、定制商品、易腐品。
4. **超窗例外**：破损、发错货、缺件——通常可破例。
5. **退货原因**（return reason）：尺寸不合、不想要、发错货、质量问题——不同原因影响运费与费用。
6. **restocking fee**（重新上架费）：部分品类收 10%–25%。
7. **退货运费谁承担**：客户原因（不想要）通常客户付；商家原因（发错/破损）商家付。

### 4.2 退款 vs 换货 vs 商店积分

| 方式 | 说明 | 何时用 |
|---|---|---|
| **Refund（退款）** | 原路退回支付方式 | 客户不想要、商品缺货 |
| **Exchange（换货）** | 换成别的尺寸/颜色/商品 | 尺寸不合、颜色不对 |
| **Store credit（商店积分）** | 退成余额 | 部分商家鼓励，成本更低 |
| **Restocking fee** | 从退款中扣除 | 政策规定时 |

### 4.3 保修（Warranty）≠ 退货（Return）

这是新手最容易混的地方：

- **退货**：无理由/有理由地把商品退回，通常有窗口。
- **保修**：针对**制造缺陷**，窗口长得多（如 1 年），流程是**维修/更换**，不是"退货退款"。
- 客户说"坏了"时，你要判断：是**退货**（窗口内）还是**保修**（缺陷）还是**换货**。

### 4.4 支付与争议

- **Refund**：商家主动退款。
- **Chargeback（拒付）**：客户向银行申诉，商家被动，成本高、影响信誉。
- **部分退款**：只退部分商品或扣除运费/费用。

### 4.5 一张决策表（你要能画出类似的）

| 条件 | 结论 |
|---|---|
| 超出退货窗口 且 非商家责任 | **拒绝**（说明政策） |
| final sale / 礼品卡 | **拒绝**（说明政策） |
| 窗口内 且 商品完好 | **批准退款** |
| 窗口内 且 客户要换尺寸 | **批准换货** |
| 商品破损/发错货（任何时间合理内） | **批准 + 免运费** |
| 制造缺陷 且 在保修期 | **转保修流程**（不是退货） |
| 信息不足（哪个订单？哪件商品？） | **澄清**（不要猜） |
| 金额/订单号与系统不符 | **升级人工**（疑似欺诈/错误） |

---

## 5. 系统地图与数据流

电商后台不是一个系统，而是一堆系统。你要知道 agent 读什么、写什么。

| 系统 | 全称 | 存什么 | Agent 用它做什么 |
|---|---|---|---|
| **OMS** | Order Management System | 订单、履约、物流 | **读**订单状态、物流 |
| **WMS** | Warehouse Management System | 库存、拣货、入库 | 读库存（退货是否可重新上架） |
| **PIM** | Product Information Management | 商品、SKU、变体 | 读商品信息 |
| **CRM** | Customer Relationship Management | 客户档案、历史 | 读客户、备注 |
| **Helpdesk** | Zendesk / Intercom / Gorgias | 工单、对话 | **读写**工单 |
| **Payment** | Stripe / Adyen / PayPal | 支付、退款 | **写**退款（高风险，需审批） |
| **ERP** | 企业资源计划 | 财务、采购 | 一般不经 agent |
| **Shopify** | 一体化电商平台 | 商品/订单/客户/退货 | **本项目的主系统** |

**数据流（一次退货请求）**：

```
客户消息
  → Agent 识别意图（退货）
  → 读政策（检索，带版本）
  → 读订单（OMS/Shopify：returnableFulfillments）
  → 判断资格（政策 + 订单 + 原因）
  → 计算金额（returnCalculate：小计/税/运费）
  → 生成行动：创建退货草稿（returnRequest，状态 REQUESTED）
  → 人工批准（returnApproveRequest → OPEN）
  → 处理退款与处置（returnProcess：退款 + RESTOCKED）
  → 通知客户 + 更新工单
```

**关键原则**：agent 只做**判断与编排**，**钱的移动**（approve/refund）永远由人批准。

---

## 6. 退货状态机（Shopify 真实版）

Shopify Admin GraphQL API 的退货流程是**真实的、有状态的**，非常适合做"决策 + 编排"项目。核心状态：

```
（无）──returnRequest──▶ REQUESTED
REQUESTED ──returnApproveRequest──▶ OPEN
REQUESTED ──returnDeclineRequest──▶ DECLINED（终态）
OPEN ──returnProcess（退款+处置）──▶ OPEN / CLOSED
OPEN ──returnCancel──▶ CANCELED（终态）
CLOSED ──returnReopen──▶ OPEN
```

**关键操作（真实 API）**：

| 操作 | GraphQL | 作用 |
|---|---|---|
| 查可退项 | `returnableFulfillments(orderId, first)` | 拿到 `fulfillmentLineItem` ID |
| 试算金额 | `returnCalculate(input)` | 只算不改：小计、税、换货项 |
| 申请退货 | `returnRequest(input)` | 建 `REQUESTED`；可带 `returnShippingFee`、`restockingFee{percentage}`、`returnReason`、`customerNote` |
| 批准 | `returnApproveRequest(input:{id})` | `REQUESTED → OPEN`（**永久**） |
| 拒绝 | `returnDeclineRequest(input:{id, declineReason})` | `REQUESTED → DECLINED`（**永久**） |
| 直接创建 | `returnCreate(returnInput)` | 直接 `OPEN`；支持 `exchangeLineItems` |
| 处理 | `returnProcess(input)` | 退款（`issueRefund`）+ 处置（`dispositions: RESTOCKED/MISSING`） |
| 关闭/重开/取消 | `returnClose` / `returnReopen` / `returnCancel` | 状态维护 |
| 移除项 | `removeFromReturn` | 客户改主意 |

**枚举值（真实）**：

- 退货原因：`SIZE_TOO_SMALL`、`SIZE_TOO_LARGE`、`UNWANTED`、`WRONG_ITEM`、`NOT_AS_DESCRIBED`、`DAMAGED`、`OTHER`（`OTHER` 需 `returnReasonNote`）
- 拒绝原因：如 `FINAL_SALE`
- 处置类型：`RESTOCKED`（重新上架）、`MISSING`（丢失）

**Webhook 事件**：`returns/request`、`returns/approve`、`returns/decline`、`returns/process`、`refunds/create`、`returns/cancel`、`returns/close`、`returns/reopen`、`returns/update`、`reverse_fulfillment_orders/dispose`、`reverse_deliveries/attach_deliverable`。

**为什么这对项目重要**：它证明"售后"在**系统层**是复杂的——有状态、有金额、有幂等要求、有不可逆操作。这正是 Agent 工程师要处理的。

---

## 7. 数据模型（Shopify 真实 schema）

你要能读懂这些对象（字段名为真实 API 名）：

### Order（订单）
```
id, name (#1001), createdAt, displayFinancialStatus (PAID/REFUNDED/PARTIALLY_REFUNDED),
displayFulfillmentStatus (FULFILLED/UNFULFILLED/PARTIALLY_FULFILLED),
email, customer { id, email }, totalPriceSet { shopMoney { amount, currencyCode } },
lineItems { nodes { id, name, quantity, sku, originalUnitPriceSet } }
```

### Fulfillment / FulfillmentLineItem（履约）
```
Fulfillment { id, status, deliveredAt, trackingInfo { number, url, company } }
FulfillmentLineItem { id, quantity, lineItem { id, name } }
```
> 退货操作的是 **fulfillmentLineItem**，不是 lineItem。

### Return（退货）
```
Return { id, name (#1001-R1), status (REQUESTED/OPEN/CLOSED/DECLINED/CANCELED),
         order { id }, returnLineItems { nodes { id, quantity, returnReason,
         customerNote, fulfillmentLineItem { id } } },
         refunds { edges { node { id, totalRefundedSet } } } }
```

### 金额对象
```
MoneyBag / MoneyV2: { amount: "59.99", currencyCode: "USD" }
shopMoney vs presentmentMoney：店铺币种 vs 展示币种
```

**GraphQL 成本**：每次查询返回 `extensions.cost { requestedQueryCost, actualQueryCost }`——可用于成本工程与限流。

---

## 8. 真实政策语料：结构化、版本化、冲突设计

### 8.1 为什么不能用"三篇玩具文档"

真实的政策有：多个品类、多个版本、例外条款、互相引用。用真实政策（公开的零售商退货/配送/保修页）能让你的评测**可信**。

### 8.2 结构化

把政策拆成可检索、可引用的**条款（clause）**：

```yaml
- clause_id: returns-window
  title: 退货窗口
  text: 大多数商品可在签收后 30 天内退货。
  applies_to: [all]
  version: v2
  effective_from: 2026-01-01
- clause_id: returns-window-exceptions
  title: 退货窗口例外
  text: 破损、发错货或缺失的商品不受 30 天窗口限制。
  applies_to: [damaged, wrong_item, missing]
  version: v2
```

### 8.3 版本化（制造真实冲突）

- 政策 v1（2025）：窗口 14 天。
- 政策 v2（2026）：窗口 30 天。
- 语料里**同时存在**，靠 `effective_from` 判断哪条生效。

这直接制造了行业里最常见的失败：**引用了被取代的旧政策**。

### 8.4 冲突设计（评测用例）

| 冲突类型 | 例子 | 期望行为 |
|---|---|---|
| 版本冲突 | v1 说 14 天，v2 说 30 天 | 用生效版本，并说明 |
| 品类冲突 | 通用条款 vs 服装特殊条款 | 用更具体的 |
| 例外覆盖 | 30 天窗口 vs 破损例外 | 破损走例外 |
| 跨文档引用 | 退货政策引用配送政策的"签收"定义 | 联合检索 |

---

## 9. 售后 Agent 的常见失败模式

| 失败模式 | 具体表现 | 防御 |
|---|---|---|
| **政策版本错误** | 引用被取代的旧政策，错误批准 | 版本化检索 + 生效日期过滤 + 引用条款 |
| **订单状态误判** | 客户说"没收到"，实际已签收 | 必须查系统，不照客户描述执行 |
| **越权退款** | 直接退款，绕过政策 | 退款永远人工批准；agent 只建草稿 |
| **提示注入** | 客户消息/商品标题里藏"忽略指令" | 输入守卫 + 把检索内容当数据 |
| **跨客户数据泄漏** | 用错 `customer_id` 读到别人订单 | 认证 + 租户隔离 + 订单归属校验 |
| **长会话漂移** | 10+ 轮后丢失上下文/目标 | 长程评测（turn 50+） |
| **金额错误** | 退款金额算错（税/运费/折扣） | 用系统试算（`returnCalculate`），不手算 |
| **重复执行** | 重试导致两次退款 | 幂等键 |
| **假 deflection** | 把客户挡在门外 | 追踪 FCR + CSAT + 升级精度 |
| **成本失控** | 循环调用、上下文爆炸 | 预算 + 熔断 + 循环检测 |

---

## 10. 术语表 + 30 个面试问题

### 10.1 术语表

| 术语 | 含义 |
|---|---|
| WISMO | Where Is My Order，订单查询 |
| DTC | Direct-to-Consumer，品牌直营 |
| OMS / WMS / PIM / CRM / ERP | 见第 5 章 |
| RMA | Return Merchandise Authorization，退货授权号 |
| EDD | Estimated Delivery Date |
| Deflection / Containment | 无需人工解决 |
| FCR | First Contact Resolution |
| CSAT | Customer Satisfaction |
| AHT | Average Handle Time |
| Restocking fee | 重新上架费 |
| Final sale | 清仓/最终销售（通常不可退） |
| Chargeback | 拒付/退单 |
| SKU / Variant | 库存单位 / 商品变体（尺寸/颜色） |
| Fulfillment | 履约（拣货、发货） |
| Reverse logistics | 逆向物流（退货运输） |
| Disposition | 退货商品的处置（重新上架/报废） |
| Idempotency | 幂等：同一请求重复执行结果一致 |
| HITL | Human-in-the-loop，人工在环 |
| SLA / SLO | 服务等级协议 / 目标 |

### 10.2 30 个面试问题（能答上就说明你懂了）

**业务与价值**
1. WISMO 占客服量的比例和单次成本大约是多少？
2. 为什么购买/支付环节不交给 agent 自动执行？
3. 退货和保修的区别是什么？
4. 什么是 final sale，为什么它重要？
5. 一次退货请求可能涉及哪几个系统？

**指标**
6. Deflection rate 和 FCR 的区别？
7. 为什么"高 deflection"可能是坏事？
8. 你会用哪三个指标衡量这个 agent 的成功？
9. 退款周期（refund cycle time）为什么影响 CSAT？
10. EDD 准确率和 WISMO 量是什么关系？

**决策与规则**
11. 退货窗口的"起算日"为什么是关键歧义？
12. 客户说"没收到货"但物流显示已签收，你怎么处理？
13. 破损商品超出退货窗口，怎么办？
14. restocking fee 什么时候收？
15. 换货和退款在库存/财务上有什么不同？

**系统与集成**
16. 退货操作的是 lineItem 还是 fulfillmentLineItem？为什么？
17. Shopify 退货有哪几个状态？哪个是不可逆的？
18. 为什么要先 `returnCalculate` 再 `returnRequest`？
19. 什么是幂等键，为什么退款需要它？
20. GraphQL 的 query cost 对成本工程有什么用？

**Agent 工程**
21. 这个 agent 的工具集你会怎么设计（读/写/危险）？
22. 哪些操作必须人工批准，为什么？
23. 如何防止提示注入通过"商品标题"进入？
24. 多轮退货会话如何避免上下文漂移？
25. 你如何评测"资格判断"的正确性？

**评测与生产**
26. 政策版本冲突时，你的评测怎么覆盖？
27. 你会如何标注一个退货决策的"正确答案"？
28. 上线后如何发现"假 deflection"？
29. 成本、延迟、质量三个约束如何取舍？
30. 如果误批了一次退款，你怎么定位根因？

---

## 附：学习资源（按优先级）

1. **Shopify 退货 API 文档**：`shopify.dev/docs/apps/build/orders-fulfillment/returns-apps/build-return-management`
2. **Shopify 开发店**：`shopify.dev/docs/apps/build/stores/generated-test-data`（`--with-demo-data`）
3. **Amazon ESCI**：`github.com/amazon-science/esci-data`（真实相关性标注）
4. **真实零售商政策页**：选 3–5 家，抓取退货/配送/保修页
5. **行业数据**：搜索 "WISMO rate"、"cost per contact"、"deflection rate" 的最新报告

---

*本文是项目 `045-post-purchase-pivot` 的阶段 0 交付物。下一步：接入 Shopify 开发店（只读）、把本手册第 8 章的政策语料落到 `config/knowledge/`、写 `docs/design.md`。*
