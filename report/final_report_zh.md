# Python `marshal` 模块稳定性与正确性测试报告

仓库地址：<https://github.com/Molingspance/marshal-testing-project>

## 1 Introduction

`marshal` 模块是 Python 标准库中的一个基础组件，主要用于对象的序列化与反序列化。所谓“序列化”，是指将某些 Python 内部对象转换为字节流；而“反序列化”则是将字节流重新还原为对应的对象结构。`marshal` 常见于 `.pyc` 文件处理等场景，因此它虽然不像 `json` 那样面向通用数据交换，却在 Python 运行时生态中具有重要地位。

尽管 `marshal` 功能明确，但在实际使用中，开发者仍然会关心它的稳定性与正确性。特别是在不同执行环境、不同 Python 版本、特殊浮点值、递归结构以及复杂容器对象下，人们通常会追问一个核心问题：对于相同的输入对象，`marshal` 是否总能产生完全一致的输出字节流；在反序列化后，得到的对象是否仍与原始对象等价。

`marshal` 的输出一致性可能受到多种因素影响，例如：

- 不同操作系统
- 不同 Python 版本
- 浮点数特殊值与符号位处理
- 递归结构与共享引用
- 无序容器的内部迭代顺序

因此，本项目围绕 `marshal` 的稳定性与正确性设计了一套测试方案，综合采用黑盒测试和白盒测试思想，覆盖等价类划分、边界值分析、模糊测试、源码导向结构覆盖以及环境差异测试等方法，并对“相同输入是否产生 hash-identical 输出”这一问题进行系统分析。

本报告将从测试判定标准、测试设计、可追踪性矩阵、关键发现与局限性等方面，对 `marshal` 模块的测试过程和结论进行说明。

### 1.1 Test Oracles

由于 `marshal` 的行为不能仅靠普通相等比较来判断，本项目定义了多种测试 oracle 来支撑后续分析：

- Round-trip oracle：对于合法对象 `x`，`marshal.loads(marshal.dumps(x))` 应恢复出与 `x` 等价的对象。
- Hash stability oracle：对于同一对象，多次执行 `marshal.dumps(x)` 应产生 SHA-256 一致的字节流。
- Exception oracle：对于不支持的对象或损坏的字节流，系统应抛出合理异常，而不是崩溃。
- Structural equivalence oracle：针对 `NaN`、`-0.0`、递归结构、共享引用与代码对象，使用自定义等价判定逻辑，而不是单纯依赖 `==`。

## 2 Black-Box Testing

黑盒测试的目标，是从使用者视角评估并验证 `marshal` 模块的稳定性与正确性。我们不依赖其内部实现细节，而是以“相同输入是否产生相同输出”“反序列化后对象是否仍正确”为核心标准，通过输入设计与结果比对来发现潜在缺陷、边界问题和环境敏感行为。

为初步理解 `marshal` 的行为，我们首先选取完全相同的输入对象，测试 `marshal.dumps(obj)` 是否始终产生一致的序列化输出，特别是在不同数据类型和边界场景下。为此，黑盒测试部分主要采用以下几种方法：

- 等价类划分
- 边界值分析
- 模糊测试

### 2.1 Equivalence Class Partitioning

通过选择具有代表性的对象类型，可以模拟 `marshal` 在常见真实场景中可能处理的主要输入类型，并验证其在不同对象类别上的序列化稳定性。该方法能够帮助我们识别某一特定类型是否更容易引发不一致输出，也为后续环境差异测试提供稳定样本。

本项目构造的等价类主要覆盖以下几类：

- 基本原子类型：`None`、`bool`、`int`、`float`、`complex`、`str`、`bytes`
- 复合容器结构：`list`、`tuple`、`dict`、`set`、`frozenset`
- 特殊结构对象：递归 list、递归 dict、间接递归结构、共享引用结构
- 特殊可序列化对象：`code object`
- 非法对象类型：函数、lambda、生成器、普通类实例、文件句柄

这种划分方式的原因在于：不同对象类型通常会进入不同的 marshal 处理路径，因此只要覆盖了主要等价类，就能较有效地覆盖用户最常接触到的输入空间。

本项目中相应的代表样例由 `src/specimens.py` 构造，并由 `tests/test_roundtrip.py` 和 `tests/test_invalid_inputs.py` 调用验证。

### 2.2 Boundary Value Analysis

由于许多问题往往出现在极端边界值附近，本项目针对 `marshal` 可能遇到的数值边界、特殊状态和边缘结构设计了专门的测试用例，直接验证其在关键条件下的稳定性与正确性。

边界测试主要包括：

- 整数边界：`-1`、`0`、`1`、`255`、`256`、`2**31 - 1`、`2**31`、`2**63 - 1`、`2**63`、超大整数
- 特殊浮点值：`inf`、`-inf`、`NaN`、`-0.0`
- 空对象：空列表、空字典、空字符串、空 bytes
- 大规模对象：长字符串、大 bytes、大列表、大 tuple、大字典
- 嵌套结构：多层嵌套 list / dict

这些边界值的选择，是因为它们更容易暴露编码表示变化、符号位丢失、空结构特殊处理以及大对象处理上的问题。

相应测试主要位于：

- `tests/test_boundaries.py`

### 2.3 Fuzz Testing

模糊测试通过自动化生成大量复杂、随机、非人工枚举的输入对象，来测试 `marshal` 在非常规输入下的稳定性与鲁棒性。与边界值分析和等价类划分不同，模糊测试并不依赖预设的固定值，而是通过程序化方式探索更大的输入空间。

本项目采用了两种模糊测试形式：

- Generation-based fuzzing：基于递归 grammar 生成合法 Python 对象，并验证 round-trip 与 repeated dumps 的稳定性
- Lexical fuzzing：对已有 marshal 字节流进行截断、插入、bit-flip、替换 type tag、追加随机后缀等变异，测试 `marshal.loads()` 的错误处理能力

生成式 fuzzing 的对象特征包括：

- 2 到 4 层嵌套的 list / tuple / dict / set / frozenset
- 整数、字符串、浮点、`None`、布尔值、特殊浮点的混合组合
- 随机长度字符串与 bytes
- 受控的容器规模与递归深度，以平衡复杂度和执行效率

本地 fuzzing 结果表明：

- 使用固定 seed `20260607`，共执行 1000 个生成式样例，未发现 round-trip 或同进程稳定性失败
- lexical fuzzing 共生成 30 个变异字节流，其中 21 个抛出受控异常，9 个仍被成功解析为合法对象

这说明 `marshal` 在当前预算内对随机合法对象表现稳定，但对于损坏字节流，部分变异结果仍可能碰巧构成另一条合法 marshal 流。除此之外，本项目还用 `tests/test_invalid_inputs.py` 对典型非法对象和目标化的损坏字节流做了补充检查，例如函数、lambda、生成器、文件句柄、空字节流、无效 type tag 和截断对象，以验证 `marshal` 是否进入预期异常路径并抛出合理异常。

## 3 White-Box Testing

白盒测试关注 `marshal` 内部结构与实现路径的覆盖情况，目标是尽可能确保在主要语句、分支和条件路径上，同一输入对象都能产生稳定的序列化行为。本项目没有重新编译并插桩 CPython，因此没有给出精确的覆盖率百分比；相反，我们采用源码导向的代表路径覆盖方法，将 `marshal.c` 中的主要类型分发和错误路径与测试样例进行映射。

### 3.1 Statement Coverage

语句覆盖要求测试能够触发主要可执行语句。对于 `marshal` 而言，这有助于验证所有核心对象类型都至少经过一次真实序列化路径，从而检查是否存在遗漏类型、未处理结构或异常路径未触发的问题。

本项目围绕 `marshal` 的主要对象处理语句设计了测试输入，重点覆盖：

- `None`、`True`、`False`、`Ellipsis`、`StopIteration`
- `int`、`float`、`complex`
- `str`、`bytes`
- `list`、`tuple`、`dict`
- `set`、`frozenset`
- `code object`
- 递归结构与共享引用
- 非法对象和损坏字节流的异常路径

我们优先确保每一类主要处理语句都被代表样例触发，并结合 round-trip 与稳定性检查，对这些语句路径上的输出进行验证。

对应的代表路径整理在：

- `results/source_checklist.md`

### 3.2 Branch Coverage

分支覆盖要求所有关键决策点都被测试，例如类型判断、异常路径、递归引用处理以及无序容器在不同环境下的行为差异。对于 `marshal` 来说，不同分支的实现方式可能导致不同的序列化结果，因此分支覆盖对于验证“相同输入是否在所有分支实现下都保持一致输出”非常重要。

本项目显式覆盖了以下主要分支：

- 合法对象成功序列化 / 非法对象抛出异常
- 合法字节流成功加载 / 损坏字节流抛出异常
- 普通容器分支 / 递归容器分支 / 共享引用分支
- 普通浮点值分支 / `NaN` 与 `-0.0` 特殊比较分支
- 同进程稳定分支 / 环境扰动下不稳定分支

特别是 `set_strings` 和 `frozenset_strings` 的测试揭示了：在不同 `PYTHONHASHSEED` 下，同一逻辑输入对象可能产生不同的 marshal 字节流，这一结果正是典型的环境敏感分支行为。

代表测试包括：

- `tests/test_cycles.py`
- `tests/test_invalid_inputs.py`
- `tests/test_determinism.py`

### 3.3 Condition Coverage

条件覆盖关注每一个布尔条件在 True 和 False 两种情况下是否都被触发。对于 `marshal` 来说，这种覆盖方式可以更细粒度地验证某些特殊条件是否会影响最终的字节流表示。

本项目重点分析并触发了以下关键条件：

- 一个浮点值是否为 `NaN`
- 一个零值浮点数是否带负号
- 容器是否为空
- 容器是否包含递归引用
- 输入字节流是否被截断
- 首字节的 type tag 是否非法
- 无序容器的迭代顺序是否受运行环境影响

这些条件分别通过如下测试样例触发：

- `float_nan`
- `float_negative_zero`
- `list_empty` / `dict_empty`
- `recursive_list` / `recursive_dict`
- `invalid-tag` / `truncated-list`
- `set_strings` / `frozenset_strings`

因此，本项目的 condition coverage 体现为“关键条件均被代表性样例触发并验证”，而不是自动化插桩后的数值化覆盖率结果。

## 4 Compatibility Testing

`marshal` 的输出结果可能受到运行环境因素影响。兼容性测试的目的，是在不同 Python 版本、不同操作系统以及不同执行环境扰动下，对相同测试对象进行比较，从而更进一步理解环境对 `marshal` 输出的影响。

本项目重点关注以下环境因素：

- 不同操作系统
- 不同 Python 版本
- 同一操作系统下不同进程环境扰动

### 4.1 Different Operating Systems

作业要求明确提到：在相同 Python 版本下，`marshal` 的输出应尽量在不同操作系统间保持一致。因此，操作系统测试是本项目兼容性分析的重要组成部分。

项目已经为以下平台准备了 CI 测试矩阵：

- Windows
- Linux
- macOS

对应配置位于：

- `.github/workflows/tests.yml`

需要如实说明的是：当前打包进 `results/` 的结果主要来自本地 Windows 环境，因此本报告尚未展示完整的多操作系统实测对比数据。这意味着操作系统兼容性测试在本项目中已被设计并自动化配置，但本地证据仍以 Windows 为主。

### 4.2 Different Python Versions

作业同样明确提到了不同 Python 版本的影响。由于 `marshal` 官方本就不保证跨版本格式稳定，因此：

- 不同版本之间若出现不同字节流，不应直接视为 bug
- 但这种差异仍然是稳定性分析的重要对象

项目准备的版本矩阵包括：

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

而本地当前报告中的实际打包证据使用的是：

- Python 3.9.15

因此，跨版本兼容性在本报告中体现为“测试设计与 CI 准备已覆盖”，而不是“本地报告中已经展示了所有版本的实测结果”。

### 4.3 Same-OS Environment Variation

除了操作系统和 Python 版本，本项目还补充了同一操作系统下的执行环境扰动测试。具体而言，我们在不同 `PYTHONHASHSEED` 下启动新进程，对相同对象重复执行 `marshal.dumps()`，并比较其 SHA-256 值。

本地关键结果如下：

- `set_strings` 在 4 个 seed 下产生了 4 个不同 hash
- `frozenset_strings` 在 4 个 seed 下产生了 4 个不同 hash
- `dict_string_keys`、`dict_different_insertion_order`、`set_ints`、递归结构、共享引用和固定文件名代码对象在本地结果中保持稳定

这说明：即使不更换操作系统，仅仅改变同一系统中的进程环境，也可能影响某些输入对象的 marshal 字节流稳定性，尤其是包含字符串元素的无序容器。

## 5 Traceability Matrix

| Test Objective / Requirement | Equivalence Class Example | Boundary Value Example | Fuzz Testing Example | Compatibility Testing Example |
| --- | --- | --- | --- | --- |
| Stability verification: identical input produces identical output | `dict_string_keys` | `int_256`, `float_negative_zero` | generated nested containers | `results/hashes.json` |
| Correctness verification: objects remain equivalent after round-trip | `string_unicode`, `list_nested` | `float_nan`, `bytes_all_byte_values` | generated legal values | same-version repeated dumps |
| Basic type processing | `int_one`, `float_one`, `string_ascii` | `int_huge`, `float_inf` | random scalar generation | same OS / same version |
| Compound structure processing | `tuple_nested`, `dict_nested` | `list_large`, `dict_large` | nested random containers | subprocess matrix |
| Special structure processing | `recursive_list`, `recursive_dict`, `shared_reference_list` | indirect recursion | generated nested recursion-free structures | same seed vs. different seed |
| Extreme value processing | representative integer / float classes | `2**63`, `NaN`, `-0.0` | random large-range numbers | version matrix |
| Empty structure processing | `list_empty`, `dict_empty`, `bytes_empty` | empty values | random empty containers | same OS repeated runs |
| Deep nesting processing | `list_nested`, `dict_nested` | large nested cases | recursive grammar generation | subprocess reruns |
| Invalid input handling | unsupported function / file handle | truncated stream | mutated byte streams | repeated environment execution |

## 6 Key Findings

通过黑盒测试和白盒测试，本项目得到以下几个关键发现。

### 6.1 String-Based Sets Cause Output Differences Under Different `PYTHONHASHSEED`

现象：对于 `set_strings` 和 `frozenset_strings`，在不同 `PYTHONHASHSEED` 下，`marshal.dumps()` 产生的字节流 hash 不同。

原因：`set` 和 `frozenset` 本质上是无序容器，而字符串元素的迭代顺序会受到 hash seed 影响。因此，即使输入逻辑上完全相同，也不能保证其 marshal 输出在不同进程环境下字节级一致。

### 6.2 Round-Trip Correctness Holds for Representative Valid Inputs

现象：对于本项目覆盖到的代表性合法输入，包括基础类型、嵌套容器、递归结构、共享引用和代码对象，`marshal.loads(marshal.dumps(x))` 均能恢复出与原对象等价的结构。

原因：`marshal` 的核心目标本就更偏向对象恢复而非跨环境字节流一致性。在当前测试范围内，它在“对象是否能正确还原”这一点上表现良好。

### 6.3 Corrupted Byte Streams Do Not Always Fail

现象：在 lexical fuzzing 中，30 个变异字节流中有 9 个仍被成功解析，而不是抛出异常。

原因：部分损坏方式只是把原始字节流变成了另一条仍然合法的 marshal 编码，或者是在完整对象之后附加了不会阻止解析的尾部数据。因此，面对损坏输入时，不能简单假设“变异后一定失败”。

## 7 Limitations and Recommendations

尽管本项目较系统地覆盖了 `marshal` 在不同输入类型和环境因素下的行为，但仍存在以下局限与改进空间：

1. 当前测试主要基于本地 Windows + Python 3.9.15 结果，跨操作系统和跨 Python 版本的完整实测证据尚未全部展示。
2. 白盒测试采用的是源码导向代表路径覆盖，而不是插桩后的精确 statement / branch / condition 覆盖率。
3. 本项目没有进行 mutation testing，也没有计算 mutation score。
4. fuzzing 只能增加信心，不能证明不存在缺陷。
5. 极深嵌套结构、极大对象和更多特殊平台架构仍可能存在未发现的兼容性问题。

基于当前测试结果，本项目给出如下建议：

- 如果场景要求对象在同一环境内被恢复，`marshal` 是可行的。
- 如果场景要求跨进程、跨平台或跨版本的字节级一致性，`marshal` 并不适合作为严格一致性序列化方案。
- 若需求强调稳定可控的跨环境交换，应优先考虑更明确的协议，例如 JSON、MessagePack 或自定义稳定编码方案。

## 8 Conclusion

本项目通过等价类划分、边界值分析、模糊测试、源码导向结构分析和环境差异测试，对 Python `marshal` 模块的稳定性与正确性进行了系统评估。

测试结果表明：

- `marshal` 对代表性合法输入具有良好的 round-trip 正确性
- 在同一进程内，输出通常稳定
- 但在执行环境发生变化时，特别是对于字符串集合类无序容器，字节流可能不再保持 hash-identical
- `marshal` 更适合保证对象恢复，而不适合承诺跨环境字节级一致性

总的来说，`marshal` 适合在同一运行生态内部进行对象持久化与内部数据处理；但如果场景要求严格的跨平台、跨版本、跨环境字节流一致性，则应选择更稳定、更可控的序列化方案。

## 9 AI Usage Disclosure

本报告在结构组织与措辞润色过程中使用了 AI 辅助，但最终内容均由作者结合真实测试结果人工审阅、修改与整理。
