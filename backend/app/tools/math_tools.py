"""数学计算工具集（SymPy + cvxpy）。

供 chat/teach agent 通过 `llm.bind_tools()` 挂载，LLM 可在需要精确符号推导
或数值最优解时主动调用。

依赖入口:
    from app.tools.math_tools import create_math_tools
    tools = create_math_tools()   # -> [SymbolicMathTool, ConvexOptimizationTool]
    llm_with_tools = llm.bind_tools(tools)

工具设计原则:
    1. LLM 只需要写"数学表达式字符串"（如 '5*x + 3*y'、'x**2 + sin(y)'），
       复杂的 Python 语法（变量声明、循环、控制流）一律不接。
    2. 任何解析/求解异常都被捕获并转成可读消息回灌给 LLM，让 LLM 自我修正。
    3. 数值结果同时给 LaTeX（符号）与小数（数值），便于 LLM 写论文时复用。
"""

from __future__ import annotations

import json
import logging
import re
from typing import ClassVar

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────
# SymbolicMathTool — SymPy 符号计算
# ────────────────────────────────────────────────────────────────────

# 会被 sympy 解析器识别的"已知函数"前缀，避免被当作变量名
_SYM_RESERVED = {
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "atan2",
    "sinh",
    "cosh",
    "tanh",
    "exp",
    "log",
    "ln",
    "sqrt",
    "cbrt",
    "Abs",
    "sign",
    "Min",
    "Max",
    "pi",
    "E",
    "I",
    "oo",
    "zoo",
    "nan",
    "diff",
    "integrate",
    "limit",
    "Sum",
    "Product",
    "factorial",
    "binomial",
    "Rational",
    "Integer",
    "Float",
    "Symbol",
    "Function",
    "Matrix",
    "True",
    "False",
    "None",
}


class SymbolicMathInput(BaseModel):
    """符号数学工具的输入 schema。LLM 直接填表达式+操作。"""

    expression: str = Field(
        description=(
            "符号数学表达式，使用 Python 语法（** 表示幂，* 表示乘）。"
            "可用符号：x, y, z, t, a, b, c 等单字母名。常见函数：sin, cos, exp, log, sqrt。"
            "示例: 'x**2 + 2*x + 1'、'sin(x)*exp(-x)'、'exp(x) - 1'"
        )
    )
    operation: str = Field(
        description=(
            "要执行的操作，可选值（不区分大小写）: "
            "'differentiate'(求导), 'integrate'(不定积分), 'integrate_def'(定积分), "
            "'solve'(代数方程/方程组), 'limit'(极限), 'series'(泰勒展开), "
            "'simplify'(化简), 'factor'(因式分解), 'expand'(展开), "
            "'dsolve'(常微分方程), 'matrix_eigen'(矩阵特征值与特征向量)"
        )
    )
    variable: str = Field(
        default="x",
        description="主变量（differentiate/integrate/solve/limit/series 用），默认 'x'。",
    )
    extra: str = Field(
        default="",
        description=(
            "附加参数 JSON 字符串（按 operation 不同含义不同）: "
            '- integrate_def: \'{"lower": 0, "upper": 1}\' 定积分上下限'
            '- limit: \'{"point": 0, "direction": "+"}\' 极限点和方向(+/-/both)'
            '- series: \'{"point": 0, "order": 6}\' 展开点和阶数'
            '- dsolve: \'{"func": "y"}\' 因变量函数名（默认 y(x)）'
            "- solve: 可省，solve 默认解关于 variable 的方程"
        ),
    )


class SymbolicMathTool(BaseTool):
    """SymPy 符号计算工具。"""

    name: ClassVar[str] = "sympy_compute"
    description: ClassVar[str] = (
        "用 SymPy 做符号数学计算：求导、积分（不定/定）、代数方程求解、常微分方程(ODE)求解、"
        "极限、泰勒展开、化简、因式分解、展开、矩阵特征值等。"
        "当你需要精确的符号推导结果（如公式、解析解、变换后的形式），或要让论文中给出"
        "LaTeX 公式时调用。返回 LaTeX 与纯文本两套结果。"
    )
    args_schema: ClassVar[type[BaseModel]] = SymbolicMathInput

    def _run(
        self,
        expression: str,
        operation: str,
        variable: str = "x",
        extra: str = "",
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            import sympy as sp
        except ImportError:
            return "错误: sympy 未安装。请运行 `pip install sympy`"

        try:
            op = operation.lower().strip()
            extra_dict = _parse_extra(extra)

            # 自动从表达式中提取符号，建立 locals 字典
            local_syms = _extract_symbols(expression)
            local_dict: dict = {}
            for s in local_syms:
                local_dict[s] = sp.Symbol(s, real=True)
            # 还要加上 variable（即使表达式里没出现也加上）
            if variable and variable not in local_dict:
                local_dict[variable] = sp.Symbol(variable, real=True)

            # dsolve 特殊: expression 含 func_name(var) 调用，须把 func_name
            # 在 local_dict 里置为 Function("name")，否则 sympify 会把它当 Symbol，
            # 之后 func_name(x) 触发 'Symbol' is not callable。
            if op == "dsolve":
                func_name = extra_dict.get("func", "y")
                local_dict.pop(func_name, None)
                local_dict[func_name] = sp.Function(func_name)

            expr = sp.sympify(expression, locals=local_dict)
            x = local_dict.get(variable, sp.Symbol(variable, real=True))

            if op == "differentiate":
                result = sp.diff(expr, x)
                return _format_sympy(result, op, variable)

            if op == "integrate":
                result = sp.integrate(expr, x)
                return _format_sympy(result, op, variable)

            if op == "integrate_def":
                lower = sp.sympify(str(extra_dict.get("lower", 0)), locals=local_dict)
                upper = sp.sympify(str(extra_dict.get("upper", 1)), locals=local_dict)
                result = sp.integrate(expr, (x, lower, upper))
                return _format_sympy(result, op, variable, extra=f"上下限 [{lower}, {upper}]")

            if op == "solve":
                # 支持多解；sympy.solve 接受表达式或列表
                result = sp.solve(expr, x, dict=True)
                # 若 expr 已是 equation 形式（sp.Eq），则直接解
                if not result:
                    result = sp.solve(sp.Eq(expr, 0), x, dict=True)
                return _format_sympy_solutions(result, variable)

            if op == "limit":
                point = sp.sympify(str(extra_dict.get("point", 0)), locals=local_dict)
                direction = extra_dict.get("direction", "+")
                result = sp.limit(expr, x, point, direction)
                return _format_sympy(result, op, variable, extra=f"x→{point}")

            if op == "series":
                point = sp.sympify(str(extra_dict.get("point", 0)), locals=local_dict)
                order = int(extra_dict.get("order", 6))
                result = sp.series(expr, x, point, order)
                return _format_sympy(
                    result.removeO(), op, variable, extra=f"在 {point} 展开到 {order} 阶"
                )

            if op == "simplify":
                return _format_sympy(sp.simplify(expr), op, variable)

            if op == "factor":
                return _format_sympy(sp.factor(expr), op, variable)

            if op == "expand":
                return _format_sympy(sp.expand(expr), op, variable)

            if op == "dsolve":
                # dsolve 已在前面把 func_name 在 local_dict 中置为 Function
                f_of_x = sp.Function(func_name)(x)
                if isinstance(expr, sp.Equality):
                    result = sp.dsolve(expr, f_of_x)
                elif expr.is_Relational or hasattr(expr, "rel_op"):
                    result = sp.dsolve(expr, f_of_x)
                else:
                    result = sp.dsolve(sp.Eq(expr, 0), f_of_x)
                return _format_sympy(
                    result, op, variable, extra=f"ODE 关于 {func_name}({variable})"
                )

            if op == "matrix_eigen":
                mat = sp.Matrix(expr)
                if mat.rows != mat.cols:
                    return f"错误: 矩阵不是方阵（{mat.rows}×{mat.cols}）"
                ev = mat.eigenvals()
                evects = mat.eigenvects()
                return _format_eigen(ev, evects)

            return (
                f"未知操作: '{operation}'。\n"
                "可选: differentiate, integrate, integrate_def, solve, limit, series, "
                "simplify, factor, expand, dsolve, matrix_eigen"
            )

        except Exception as e:  # noqa: BLE001
            logger.exception("sympy_compute failed")
            return (
                f"符号计算失败: {type(e).__name__}: {e}\n"
                "请检查: 1) 表达式语法（** 表示幂，* 表示乘）  "
                "2) 变量是否在 expression 中出现或通过 variable 指定  "
                "3) 操作名是否正确（见 description）"
            )


# ────────────────────────────────────────────────────────────────────
# ConvexOptimizationTool — cvxpy 凸优化求解
# ────────────────────────────────────────────────────────────────────


class ConvexOptimizationInput(BaseModel):
    """凸优化工具的输入 schema。"""

    problem_type: str = Field(
        default="LP",
        description=(
            "凸优化问题类型，可选: 'LP'(线性规划), 'QP'(二次规划), "
            "'IP'(整数规划/MIP), 'SOCP'(二阶锥规划)"
        ),
    )
    sense: str = Field(
        default="minimize",
        description="'minimize' 或 'maximize'",
    )
    objective: str = Field(
        description=(
            "目标函数（数学表达式字符串）。可用变量: x, y, z, w 等。"
            "LP/IP 示例: '5*x + 3*y'; QP 示例: 'x**2 + (y-1)**2'; "
            "SOCP 示例: 'cp.norm(cp.vstack([x-1, y-2]), 2)'"
        )
    )
    variables: str = Field(
        default="[]",
        description=(
            "变量定义 JSON 数组。每项可为: \n"
            "  - 'x'                连续变量 x\n"
            "  - 'x >= 0'           连续变量 x 且 x >= 0\n"
            "  - 'z: integer'       整数变量 z（IP 用）\n"
            "  - 'w: boolean'       0/1 变量 w（IP 用）\n"
            '示例: \'["x >= 0", "y >= 0", "z: integer"]\''
        ),
    )
    constraints: str = Field(
        default="[]",
        description=(
            "约束列表 JSON 数组，每项是一个 Python 表达式，支持: "
            "'<='、'>='、'==' 三种关系。\n"
            '示例: \'["x + y <= 10", "2*x - y >= 5", "x >= 0", "y >= 0"]\''
        ),
    )


class ConvexOptimizationTool(BaseTool):
    """cvxpy 凸优化求解工具。"""

    name: ClassVar[str] = "solve_optimization"
    description: ClassVar[str] = (
        "用 cvxpy 求解凸优化问题（LP 线性规划 / QP 二次规划 / IP 整数规划 / SOCP 二阶锥规划）。"
        "适用于资源分配、运输问题、投资组合、排产调度、配送路径等需要给出**具体数值最优解**的场景。"
        "返回最优解（每个变量的数值）、最优值、求解器与状态。"
    )
    args_schema: ClassVar[type[BaseModel]] = ConvexOptimizationInput

    def _run(
        self,
        problem_type: str,
        objective: str,
        variables: str = "[]",
        constraints: str = "[]",
        sense: str = "minimize",
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            import cvxpy as cp
            import sympy as sp
        except ImportError as e:
            return f"错误: 缺少依赖 {e.name}。请运行 `pip install cvxpy`"

        try:
            pt = problem_type.upper().strip()
            if pt not in ("LP", "QP", "IP", "SOCP"):
                return f"不支持的问题类型: '{problem_type}'，可选: LP, QP, IP, SOCP"

            sn = sense.lower().strip()
            if sn not in ("minimize", "maximize"):
                return f"未知 sense: '{sense}'，可选: minimize, maximize"

            # 1. 解析变量
            try:
                var_specs = json.loads(variables) if variables.strip() else []
            except json.JSONDecodeError as e:
                return f"variables 不是合法 JSON: {e}\n原始: {variables}"

            var_map: dict = {}
            extra_constraints: list = []
            spec_errors: list = []
            for spec in var_specs:
                if not isinstance(spec, str):
                    spec_errors.append(f"变量项必须是字符串，得到 {type(spec).__name__}: {spec!r}")
                    continue
                s = spec.strip()
                if ":" in s:
                    name, kind = [x.strip() for x in s.split(":", 1)]
                    if not name.isidentifier():
                        spec_errors.append(f"变量名非法: {name!r}")
                        continue
                    if kind == "integer":
                        var_map[name] = cp.Variable(name=name, integer=True)
                    elif kind in ("boolean", "binary", "bool"):
                        var_map[name] = cp.Variable(name=name, boolean=True)
                    else:
                        spec_errors.append(f"未知变量类型: {kind!r}（仅支持 integer / boolean）")
                elif ">=" in s or "<=" in s or "==" in s:
                    # 形如 "x >= 0" → 拆成变量+约束
                    m = re.match(r"\s*([A-Za-z_]\w*)\s*(>=|<=|==)\s*(.+)", s)
                    if not m:
                        spec_errors.append(f"无法解析: {s!r}")
                        continue
                    name, op, rhs_str = m.group(1), m.group(2), m.group(3)
                    if name not in var_map:
                        var_map[name] = cp.Variable(name=name)
                    # 转 sympy 后再转 cvxpy
                    sp.sympify(rhs_str)
                    cstr = _sympy_to_cvxpy(sp.sympify(f"{name} {op} {rhs_str}"), var_map)
                    extra_constraints.append(cstr)
                else:
                    # 裸变量名
                    if not s.isidentifier():
                        spec_errors.append(f"变量名非法: {s!r}")
                        continue
                    var_map[s] = cp.Variable(name=s)

            if spec_errors:
                return "变量声明有误:\n" + "\n".join(f"  - {e}" for e in spec_errors)

            if not var_map:
                return "错误: 至少声明一个变量（variables 不能为空数组）"

            # 2. 解析目标与约束（sympy → cvxpy）
            try:
                sym_obj = sp.sympify(objective)
                cp_obj = _sympy_to_cvxpy(sym_obj, var_map)
            except Exception as e:  # noqa: BLE001
                return f"目标函数解析失败: {type(e).__name__}: {e}\n请检查表达式语法"

            try:
                cstr_raw = json.loads(constraints) if constraints.strip() else []
            except json.JSONDecodeError as e:
                return f"constraints 不是合法 JSON: {e}\n原始: {constraints}"

            cvx_constraints = list(extra_constraints)
            cstr_errors: list = []
            for cstr in cstr_raw:
                if not isinstance(cstr, str):
                    cstr_errors.append(f"约束项必须是字符串，得到 {type(cstr).__name__}")
                    continue
                try:
                    sym_c = sp.sympify(cstr)
                    cvx_c = _sympy_to_cvxpy(sym_c, var_map)
                    if not isinstance(
                        cvx_c, (cp.constraints.Constraint, cp.expressions.expression.Expression)
                    ):
                        cstr_errors.append(f"约束不合法: {cstr!r}（不是 cvxpy 表达式或关系）")
                        continue
                    cvx_constraints.append(cvx_c)
                except Exception as e:  # noqa: BLE001
                    cstr_errors.append(f"约束 {cstr!r} 解析失败: {e}")
            if cstr_errors:
                return "约束解析错误:\n" + "\n".join(f"  - {e}" for e in cstr_errors)

            # 3. 构建并求解
            obj = cp.Minimize(cp_obj) if sn == "minimize" else cp.Maximize(cp_obj)
            prob = cp.Problem(obj, cvx_constraints)

            # IP/MIP 求解器选择: cvxpy 1.5+ 中 SCIPY=HiGHS（通用 MIP），ECOS_BB 仅 0/1。
            # cvxpy 求解器常量就是字符串 sentinel。
            solver_used = ""
            if pt == "IP":
                installed = set(cp.installed_solvers())  # list[str]
                # 优先级: SCIPY (HiGHS, 通用) > ECOS_BB (仅 0/1) > SCIP (若装) > SCS
                preferred = [s for s in ("SCIPY", "ECOS_BB", "SCIP", "SCS") if s in installed]
                last_err: str | None = None
                if not preferred:
                    return (
                        "错误: 当前 cvxpy 未安装能求解整数规划(MIP)的求解器。\n"
                        f"已安装求解器: {', '.join(sorted(installed)) or '(无)'}\n"
                        "请运行: pip install cvxpy[scip]   或   pip install scipy\n"
                        "（cvxpy 自带 SCIPY=HiGHS 求解器，支持整数；ECOS_BB 仅 0/1）"
                    )
                for s_name in preferred:
                    try:
                        prob.solve(solver=s_name, verbose=False)
                        solver_used = s_name
                        if prob.status in ("optimal", "optimal_inaccurate"):
                            break
                    except Exception as e:  # noqa: BLE001
                        last_err = str(e)[:300]
                        continue
                if not solver_used and last_err:
                    return f"IP 求解失败: {last_err}\n请尝试更小的整数规模或换 solver（已尝试 {preferred}）"
            else:
                prob.solve(verbose=False)
                try:
                    if prob.solver_stats:
                        solver_used = prob.solver_stats.name
                except Exception:
                    pass

            return _format_cvxpy_result(prob, var_map, pt, sn, solver_used)

        except Exception as e:  # noqa: BLE001
            logger.exception("solve_optimization failed")
            return (
                f"优化求解失败: {type(e).__name__}: {e}\n"
                "提示: 1) 目标/约束表达式用 Python 语法（** 表示幂）"
                "  2) 变量名须先在 variables 声明  "
                "3) IP 仅支持线性目标+约束"
            )


# ────────────────────────────────────────────────────────────────────
# 内部辅助
# ────────────────────────────────────────────────────────────────────


def _extract_symbols(expr: str) -> list[str]:
    """从表达式字符串中提取所有非保留的标识符作为符号名。"""
    tokens = re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\b", expr)
    seen: list[str] = []
    for t in tokens:
        if t in _SYM_RESERVED:
            continue
        if t not in seen:
            seen.append(t)
    return seen


def _parse_extra(extra: str) -> dict:
    if not extra or not extra.strip():
        return {}
    try:
        return json.loads(extra)
    except json.JSONDecodeError:
        return {}


def _sympy_to_cvxpy(expr, var_map: dict):
    """把 sympy 表达式递归转成 cvxpy 表达式或约束。

    支持: Number/Symbol/Add/Mul/Pow/常用函数/关系运算。
    变量从 var_map 查;未知符号当常数;数值直接取 float。
    """
    import cvxpy as cp
    import sympy as sp

    if isinstance(expr, (int, float)):
        return float(expr)

    if expr.is_Number:
        return float(expr)

    if expr.is_Symbol:
        name = str(expr)
        if name in var_map:
            return var_map[name]
        # 未知符号当常数（用其数值；sympy 常数 pi/E 已是 Number，会被上面截获）
        try:
            return float(expr)
        except (TypeError, ValueError):
            return expr  # 留给上层报错

    if expr.is_Add:
        return sum((_sympy_to_cvxpy(a, var_map) for a in expr.args), 0)

    if expr.is_Mul:
        result = 1
        for a in expr.args:
            result = result * _sympy_to_cvxpy(a, var_map)
        return result

    if expr.is_Pow:
        base = _sympy_to_cvxpy(expr.args[0], var_map)
        exp_v = _sympy_to_cvxpy(expr.args[1], var_map)
        return base**exp_v

    if expr.is_Relational or hasattr(expr, "rel_op"):
        lhs = _sympy_to_cvxpy(expr.lhs, var_map)
        rhs = _sympy_to_cvxpy(expr.rhs, var_map)
        rel = expr.rel_op
        if rel == "<=":
            return lhs <= rhs
        if rel == ">=":
            return lhs >= rhs
        if rel == "==":
            return lhs == rhs
        raise ValueError(f"不支持的关系: {rel}")

    # 函数
    func_map = {
        sp.sin: cp.sin,
        sp.cos: cp.cos,
        sp.tan: cp.tan,
        sp.asin: cp.arcsin,
        sp.acos: cp.arccos,
        sp.atan: cp.arctan,
        sp.sinh: cp.sinh,
        sp.cosh: cp.cosh,
        sp.tanh: cp.tanh,
        sp.exp: cp.exp,
        sp.log: cp.log,
        sp.Abs: cp.abs,
        sp.sqrt: cp.sqrt,
    }
    func = getattr(expr, "func", None)
    if func in func_map:
        arg = _sympy_to_cvxpy(expr.args[0], var_map)
        return func_map[func](arg)

    # 兜底: 当常数
    try:
        return float(expr)
    except (TypeError, ValueError):
        raise ValueError(f"无法转换 sympy 表达式为 cvxpy: {expr!r}（func={func}）")


# ── 输出格式化 ──


def _format_sympy(result, op: str, variable: str, extra: str = "") -> str:
    import sympy as sp

    extra_line = f"（{extra}）" if extra else ""
    latex = sp.latex(result)
    text = str(result)
    return (
        f"操作: {op} (变量 {variable}){extra_line}\n"
        f"LaTeX 形式:\n```latex\n{latex}\n```\n"
        f"文本形式:\n```\n{text}\n```"
    )


def _format_sympy_solutions(result, variable: str) -> str:
    import sympy as sp

    if not result:
        return f"操作: solve (变量 {variable})\n无解（可能无实数解或方程恒等/矛盾）"

    # result 形如 [{x: 1}, {x: 2}] 或 [1, 2]
    if isinstance(result, list) and result and isinstance(result[0], dict):
        lines = []
        for i, sol in enumerate(result, 1):
            parts = ", ".join(f"{k} = `{sp.latex(v)}`" for k, v in sol.items())
            lines.append(f"  {i}. {parts}")
        return f"操作: solve (变量 {variable})\n共 {len(result)} 个解：\n" + "\n".join(lines)
    if isinstance(result, list):
        lines = [f"  {i}. `{sp.latex(s)}`" for i, s in enumerate(result, 1)]
        return f"操作: solve (变量 {variable})\n共 {len(result)} 个解：\n" + "\n".join(lines)
    return _format_sympy(result, "solve", variable)


def _format_eigen(ev, evects) -> str:
    import sympy as sp

    ev_str = ", ".join(f"`{sp.latex(k)}` (重数 {v})" for k, v in ev.items())
    evect_lines = []
    for lam, mult, vects in evects:
        v_strs = []
        for v in vects:
            try:
                v_strs.append(f"`{sp.latex(v.T)}`")
            except Exception:
                v_strs.append(f"`{v}`")
        evect_lines.append(f"  λ = `{sp.latex(lam)}` (重数 {mult}): " + "; ".join(v_strs))
    return "矩阵特征值:\n" + ev_str + "\n\n特征向量:\n" + "\n".join(evect_lines)


def _format_cvxpy_result(prob, var_map: dict, pt: str, sense: str, solver_used: str = "") -> str:

    status_map = {
        "optimal": "[OK] 最优",
        "optimal_inaccurate": "[!] 最优（近似）",
        "infeasible": "[X] 不可行",
        "unbounded": "[INF] 无界（目标可无限改进）",
        "infeasible_inaccurate": "[X] 不可行（近似）",
        "unbounded_inaccurate": "[INF] 无界（近似）",
    }
    status_zh = status_map.get(prob.status, prob.status)
    solver_name = solver_used
    if not solver_name and prob.solver_stats:
        try:
            solver_name = prob.solver_stats.name
        except Exception:
            solver_name = ""

    head = f"问题类型: {pt}（{sense}）\n求解器: {solver_name or 'default'}\n状态: {status_zh}"

    if prob.status not in ("optimal", "optimal_inaccurate"):
        return (
            f"{head}\n该问题无最优解。请检查约束（infeasible/不可行）或目标方向（unbounded/无界）。"
        )

    opt_val = prob.value
    try:
        opt_str = f"{float(opt_val):.10g}"
    except (TypeError, ValueError):
        opt_str = str(opt_val)

    sol_lines = []
    for name, v in var_map.items():
        val = getattr(v, "value", None)
        if val is None:
            continue
        try:
            fv = float(val)
            if abs(fv) < 1e-12:
                fv = 0.0
            sol_lines.append(f"  {name} = {fv:.10g}")
        except (TypeError, ValueError):
            sol_lines.append(f"  {name} = {val}")

    return (
        f"{head}\n最优值: {opt_str}\n\n最优解:\n" + "\n".join(sol_lines)
        if sol_lines
        else f"{head}\n最优值: {opt_str}"
    )


# ── 工厂 ──


def create_math_tools() -> list[BaseTool]:
    """工厂：返回全部数学工具（供 llm.bind_tools()）。"""
    return [
        SymbolicMathTool(),
        ConvexOptimizationTool(),
    ]
