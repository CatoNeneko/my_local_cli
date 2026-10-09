# 折扣函数修复验收项目

`discount.py` 提供 `apply_discount(price, percent)`，返回打折后的价格，不是折扣金额。

- `price` 为非负数字；负数抛出 `ValueError`。
- `percent` 为 0～100 的数字；超出范围抛出 `ValueError`。
- 0% 返回原价；100% 返回 0；保留计算精度，不额外四舍五入。
- `test_discount.py` 是固定验收测试，不允许修改或删除。
- 请新增 `test_discount_edges.py` 验证边界和非法参数。

当前函数故意包含错误。必须先通过工具运行现有测试，观察真实失败，再修改和重新测试。
