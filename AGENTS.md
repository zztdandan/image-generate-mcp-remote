# AGENTS Handbook (image-generate-mcp-remote)

本文件定义 `image-generate-mcp-remote/` 范围内的 Python 编码规范。

## 1) 类型标注总原则

- 所有 Python 函数的入参、返回值必须显式标注类型。
- 所有类变量、实例变量必须显式标注类型。
- 禁止在业务代码的函数入参、返回值、类变量定义中直接使用 `Any`。
- 若能确定具体类型，必须写具体类型；不得为了省事退化成 `Any`、`object`、宽泛 `dict` 或宽泛 `list`。

## 2) JSON 相关类型约定

涉及通用 JSON 数据时，统一优先使用以下类型别名语义：

```python
from typing import TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONMap: TypeAlias = dict[str, JSONValue]
```

- 若值可明确为某个结构体，不得继续使用 `JSONMap` 兜底，必须定义真实类型。
- `JSONScalar` 仅用于确属标量的值；不要把有明确业务含义的字段长期保留为裸 `str` 或裸 `int`。

## 3) 枚举与常量

- 若某字段是字符串枚举或数字枚举，必须定义枚举类型，不得在代码中散落魔法字面量。
- 字符串枚举优先使用 `StrEnum`；数字枚举按语义使用 `IntEnum` 或 `Enum`。
- 真正使用该值时，应引用枚举成员，而不是再次手写原始字串或数字。
- 若某值是固定定值且具有明确业务意义，必须提取为命名常量，不得直接硬编码。

示例：

```python
from enum import StrEnum

REQUEST_STATUS_PENDING = "pending"


class RequestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
```

- 若该值属于“有限候选集合”，优先建枚举。
- 若该值属于“单一协议常量 / 元数据键 / 固定开关值”，优先建常量。

## 4) 结构化参数与返回值

- 若函数参数本质上是一个固定结构，不得使用 `tuple[...]` 位置拼装多个值传递业务语义。
- 不得使用 `dict[str, Any]`、`dict[str, object]` 表达稳定结构的入参或返回值。
- 对于稳定结构，必须定义真实类型，如 `dataclass`、`pydantic.BaseModel`、具名类。
- 若返回值包含多个具名字段，同样优先返回结构化对象，而不是匿名元组或宽泛字典。

推荐方向：

- 领域/服务层稳定载荷：优先 `dataclass` 或 `pydantic.BaseModel`
- 配置对象：优先 `BaseModel` 或明确配置类
- 协议对象：优先具名模型类与类型别名组合

## 5) 宽泛类型禁用清单

以下写法在本目录范围内默认禁止，除非是三方库边界适配且无法收窄：

- `Any`
- `dict[str, Any]`
- `list[Any]`
- `tuple[Any, ...]`
- 无业务语义的裸 `object`

如确实处于外部系统边界，必须先在边界层完成解析、校验、收窄，再进入业务代码。

## 6) 建模要求

- 参数一旦存在业务名称、业务约束、字段含义，就应建模，不要把结构藏在 tuple 下标或 dict key 里。
- 类字段类型应直接表达真实含义，例如状态、模式、资源类型、事件名，应优先使用枚举或具名类型。
- 不允许因为“当前先跑通”而省略类型；类型本身就是可读性与可靠性的一部分。

## 7) 代码评审判定标准

出现以下情况，视为不符合本规范：

- 新增函数参数或返回值含 `Any`
- 新增类字段使用 `Any`
- 业务枚举值仍以裸字符串/裸数字直接流转
- 固定结构仍以 `tuple`、`dict[str, Any]`、匿名字典传递
- 明明可以写成具体类型，却退化为宽泛类型

## 8) 落地优先级

- 第一优先级：新增代码必须完全遵守本规范。
- 第二优先级：修改旧代码时，若触达相关函数、模型、字段，应顺手把对应类型收窄到本规范要求。
- 第三优先级：所有新增协议常量、状态值、事件值、模式值，应在首次引入时完成枚举或常量化。
