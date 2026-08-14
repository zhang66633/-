# 极大似然估计

> **难度**:进阶 · **预计学习时长**:50 分钟 · **主讲智能体**:🧩 建模手 · **方法类别**:统计推断

## 🎯 学习目标

学完本单元,你应该能够:

- 说清极大似然估计的核心思想——「哪个参数值最可能产生眼前这批数据」,并据此写出似然函数
- 独立完成伯努利、正态、指数、泊松分布 MLE 的完整求导推导
- 理解 MLE 的一致性、渐近正态性与渐近有效性,以及「不变性」原理
- 识别驻点法失效的情形(边界解,如均匀分布),知道何时改用数值优化
- 理解 EM 算法的 E 步 / M 步结构,并能读懂其收敛性质

## 📖 核心概念

### 1. MLE 的思想:让数据「看起来最合理」

统计学的基本问题之一是**参数估计**:已知数据来自某个分布族 $f(x \mid \theta)$(如正态、指数、泊松),但参数 $\theta$ 未知,如何用样本把 $\theta$ 估计出来?

极大似然估计(Maximum Likelihood Estimation, MLE)的回答是:**选一个 $\theta$,使已经观测到的这批数据出现的概率(密度)最大**。

> 直觉:两个人各抛 10 次硬币,甲抛出 7 正 3 反,乙抛出 2 正 8 反。如果让你猜谁用的是一枚「偏正」的硬币,你肯定猜甲。MLE 就是把这种直觉形式化:对甲的硬币,「正面概率 $p = 0.7$」比「$p = 0.5$」更能解释 7/10 这个结果。

### 2. 似然函数与对数似然

设样本 $x_1, x_2, \dots, x_n$ 独立同分布,概率密度(或概率质量)为 $f(x \mid \theta)$。**似然函数**定义为:

$$L(\theta) = \prod_{i=1}^{n} f(x_i \mid \theta)$$

注意:**似然是参数 $\theta$ 的函数,数据是固定的**——这与「密度是 $x$ 的函数、参数固定」正好相反,是整个单元最关键的视角切换。

由于连乘在求导时极不方便,通常取对数得到**对数似然**:

$$\ell(\theta) = \ln L(\theta) = \sum_{i=1}^{n} \ln f(x_i \mid \theta)$$

因为 $\ln$ 是严格单调递增函数,$L$ 与 $\ell$ 的极大值点完全相同,而 $\ell$ 是求和形式,求导、数值计算都更友好。

### 3. 求 MLE 的标准三步

1. **写似然**:按「样本独立 → 联合密度等于各边际密度之积」写出 $L(\theta)$
2. **取对数**:$\ell(\theta) = \sum \ln f(x_i \mid \theta)$,连乘变求和
3. **求极大**:解得分方程 $\ell'(\theta) = 0$,用二阶导(或单调性)验证是极大点;别忘了**检查参数空间的边界**

> 💡 **建模心法**:竞赛中拿到数据先画直方图、判断分布形状,再对候选分布逐个做 MLE 并比较对数似然(或 AIC/BIC),这是「分布拟合」的标准动作。

### 4. MLE 的优良性质

- **一致性**:样本量 $n \to \infty$ 时,$\hat{\theta}$ 依概率收敛到真值 $\theta$
- **渐近正态**:$\sqrt{n}(\hat{\theta} - \theta)$ 渐近服从 $N(0, 1/I(\theta))$,其中 $I(\theta)$ 是 Fisher 信息
- **渐近有效**:大样本下 MLE 的方差达到 Cramér-Rao 下界,是所有渐近无偏估计中方差最小的
- **不变性**:若 $\hat{\theta}$ 是 $\theta$ 的 MLE,则对任意一一变换 $g$,$g(\hat{\theta})$ 就是 $g(\theta)$ 的 MLE。例如 $\hat{\lambda} = \bar{x}$ 是泊松参数 $\lambda$ 的 MLE,那么 $e^{-\lambda}$ 的 MLE 就是 $e^{-\bar{x}}$

### 5. 数值优化与 EM 算法

- **解析解不存在时**:对 Gamma、Weibull 等分布,得分方程没有显式解,用 Newton-Raphson 迭代 $\theta^{(t+1)} = \theta^{(t)} - \ell'(\theta^{(t)}) / \ell''(\theta^{(t)})$,或直接调 `scipy.optimize.minimize` 最小化负对数似然
- **EM 算法**:当模型含**隐变量**(看不见的量,如混合模型中的类别标签)时,似然中出现积分或求和,直接最大化困难。EM 交替执行:
  - **E 步**:用当前参数 $\theta^{(t)}$ 计算隐变量的条件期望,构造 $Q(\theta \mid \theta^{(t)})$(完全数据对数似然的期望)
  - **M 步**:$\theta^{(t+1)} = \arg\max_{\theta} Q(\theta \mid \theta^{(t)})$

  可以证明每次迭代后观测数据的对数似然**单调不降**,因此 EM 至少收敛到局部极大。高斯混合聚类、缺失数据填补都是 EM 的经典应用。

## 🧮 公式与结论

**核心公式一览**:

| 名称 | 公式 | 说明 |
|------|------|------|
| 似然函数 | $L(\theta) = \prod_{i=1}^{n} f(x_i \mid \theta)$ | 联合密度,视 $\theta$ 为变量 |
| 对数似然 | $\ell(\theta) = \sum_{i=1}^{n} \ln f(x_i \mid \theta)$ | 连乘化求和 |
| 得分方程 | $\ell'(\theta) = 0$ | 驻点条件,解后需验证极大 |
| Fisher 信息 | $I(\theta) = -E\left[\dfrac{\partial^2 \ell}{\partial \theta^2}\right]$ | 信息量,决定估计精度 |
| 渐近方差 | $\mathrm{Var}(\hat{\theta}) \approx \dfrac{1}{n I(\theta)}$ | 大样本下标准误的来源 |

**常用分布的 MLE 速查表**:

| 分布 | 密度 / 概率 | MLE |
|------|-----------|-----|
| Bernoulli $(p)$ | $p^{x}(1-p)^{1-x}$ | $\hat{p} = \bar{x}$(正面次数 / 总次数) |
| Poisson $(\lambda)$ | $e^{-\lambda}\lambda^{x} / x!$ | $\hat{\lambda} = \bar{x}$ |
| 正态 $N(\mu, \sigma^2)$ | $\dfrac{1}{\sqrt{2\pi\sigma^2}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}$ | $\hat{\mu} = \bar{x},\ \hat{\sigma}^2 = \dfrac{1}{n}\sum (x_i - \bar{x})^2$ |
| 指数 Exp $(\lambda)$ | $\lambda e^{-\lambda x}$ | $\hat{\lambda} = 1/\bar{x}$ |
| 均匀 $U(0, \theta)$ | $1/\theta,\ 0 < x < \theta$ | $\hat{\theta} = \max\{x_i\}$(边界解!) |

## 💡 经典例题

### 例题 1:抛硬币——伯努利分布的 MLE

> 抛一枚硬币 10 次,出现 7 次正面。用 MLE 估计正面概率 $p$。

**第一步:写似然函数**。设 $X \sim \text{Bernoulli}(p)$,$P(X = 1) = p$。10 次观测中 7 正 3 反,各次观测独立:

$$L(p) = p^7 (1-p)^3$$

**第二步:取对数**:

$$\ell(p) = 7\ln p + 3\ln(1-p)$$

**第三步:求导令零**:

$$\ell'(p) = \frac{7}{p} - \frac{3}{1-p} = 0 \quad \Rightarrow \quad 7(1-p) = 3p \quad \Rightarrow \quad \hat{p} = 0.7$$

**验证是极大点**:$\ell''(p) = -\dfrac{7}{p^2} - \dfrac{3}{(1-p)^2} < 0$ 恒成立,对数似然严格凹,$\hat{p} = 0.7$ 是全局最大。边界上 $p \to 0$ 或 $p \to 1$ 时 $\ell \to -\infty$,无需担心边界解。

**解析**:答案 $\hat{p} = 0.7$ 就是样本比例,完全符合直觉。注意 $\hat{p}$ 是随机变量——再抛 10 次可能得到不同估计;但抛的次数越多,$\hat{p}$ 越接近真值,这就是一致性的直观含义。

### 例题 2:正态分布——两个参数同时估计

> 已知 $X \sim N(\mu, \sigma^2)$,样本 $x_1, \dots, x_n$。求 $\mu$ 与 $\sigma^2$ 的 MLE。

**写似然**:

$$L(\mu, \sigma^2) = \prod_{i=1}^{n} \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x_i-\mu)^2}{2\sigma^2}\right)$$

**取对数**:

$$\ell(\mu, \sigma^2) = -\frac{n}{2}\ln(2\pi) - \frac{n}{2}\ln\sigma^2 - \frac{1}{2\sigma^2}\sum_{i=1}^{n}(x_i - \mu)^2$$

**对 $\mu$ 求偏导**($\sigma^2$ 视为常数):

$$\frac{\partial \ell}{\partial \mu} = \frac{1}{\sigma^2}\sum_{i=1}^{n}(x_i - \mu) = 0 \quad \Rightarrow \quad \hat{\mu} = \bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

**对 $\sigma^2$ 求偏导**(把 $\sigma^2$ 看成一个整体变量):

$$\frac{\partial \ell}{\partial \sigma^2} = -\frac{n}{2\sigma^2} + \frac{1}{2(\sigma^2)^2}\sum_{i=1}^{n}(x_i - \mu)^2 = 0 \quad \Rightarrow \quad \hat{\sigma}^2 = \frac{1}{n}\sum_{i=1}^{n}(x_i - \hat{\mu})^2$$

**数值验算**:设样本为 $(2, 4, 6)$,则 $\bar{x} = 4$,

$$\hat{\sigma}^2 = \frac{(2-4)^2 + (4-4)^2 + (6-4)^2}{3} = \frac{4+0+4}{3} = \frac{8}{3} \approx 2.667$$

**解析**:注意 $\hat{\sigma}^2$ 分母是 $n$ 而不是 $n-1$——MLE 是**有偏**估计。无偏的样本方差 $s^2 = \frac{1}{n-1}\sum(x_i - \bar{x})^2 = 4$,比 $\hat{\sigma}^2$ 略大,二者关系为 $s^2 = \frac{n}{n-1}\hat{\sigma}^2$。论文里写「极大似然估计」与「无偏估计」时务必区分。

### 例题 3:指数分布——「平均寿命」的倒数

> 某电子元件寿命 $X \sim \text{Exp}(\lambda)$(密度 $\lambda e^{-\lambda x},\ x > 0$),抽 3 件测得寿命 $0.5, 1.0, 1.5$(千小时)。估计失效率 $\lambda$。

**写似然并取对数**:

$$L(\lambda) = \prod_{i=1}^{3} \lambda e^{-\lambda x_i} = \lambda^3 e^{-\lambda (0.5 + 1.0 + 1.5)}, \qquad \ell(\lambda) = 3\ln\lambda - 3\lambda$$

**求导**:

$$\ell'(\lambda) = \frac{3}{\lambda} - 3 = 0 \quad \Rightarrow \quad \hat{\lambda} = 1$$

**验证**:$\ell''(\lambda) = -3/\lambda^2 < 0$,确为极大点。一般地,$\hat{\lambda} = n / \sum x_i = 1/\bar{x}$——平均寿命的倒数。

**解析**:$\hat{\lambda} = 1$(平均每千小时失效 1 次),平均寿命的估计为 $\hat{E}[X] = 1/\hat{\lambda} = 1$ 千小时。由**不变性**,平均寿命 $1/\lambda$ 的 MLE 就是 $1/\hat{\lambda}$;同样,「1000 小时内不失效」的概率 $P(X > 1) = e^{-\lambda}$ 的 MLE 就是 $e^{-\hat{\lambda}} = e^{-1} \approx 0.368$。

## ⚠️ 常见易错点

1. **只在驻点上找 MLE,忽略边界**。$U(0, \theta)$ 的似然 $L(\theta) = 1/\theta^n$ 关于 $\theta$ 单调递减,没有驻点,最大值在「参数空间边界」$\hat{\theta} = \max\{x_i\}$ 取到——任何小于 $\max\{x_i\}$ 的 $\theta$ 根本不可能产生这批数据(似然为 0)
2. **把 $\hat{\sigma}^2$ 当成无偏估计**。MLE 的 $\hat{\sigma}^2$ 分母是 $n$,无偏版本 $s^2$ 分母是 $n-1$;小样本下差别明显,写论文时要讲清楚用的是哪个
3. **对离散参数盲目求导**。若参数在整数集上取值(如「号码从 $1$ 到 $N$」),不能对 $\theta$ 求导,应直接比较 $L(\theta)$ 在各候选点的大小
4. **忘记「似然是 $\theta$ 的函数」**。数据一旦观测就是常数;写出 $L(\theta) = \prod f(x_i \mid \theta)$ 后不要再去「积分掉 $x$」,也不要把 $\bar{x}$ 当变量求导
5. **漏掉独立性条件**。$L(\theta) = \prod f(x_i \mid \theta)$ 只在样本独立同分布时成立;时间序列、空间相关数据不能直接连乘,应改用条件似然
6. **EM 算法中混淆隐变量与参数**。E 步计算的是隐变量 $z$ 的条件期望(责任度),M 步才更新参数 $\theta$;把两者混在一起「一并最大化」是常见错误

## ✏️ 自测练习(选择题)

**第 1 题** 设 $X \sim N(\mu, \sigma^2)$,样本为 $(2,\ 4,\ 6)$。求 $\mu$ 与 $\sigma^2$ 的极大似然估计,并指出 $\hat{\sigma}^2$ 的性质:

A. $\hat{\mu} = 4$,$\hat{\sigma}^2 = \dfrac{8}{3} \approx 2.667$(分母为 $n$),这是有偏估计
B. $\hat{\mu} = 4$,$\hat{\sigma}^2 = 4$(分母为 $n-1$),这是无偏估计
C. $\hat{\mu} = 4$,$\hat{\sigma}^2 = \dfrac{8}{3}$,且它是无偏估计
D. $\hat{\mu} = 3$,$\hat{\sigma}^2 = \dfrac{8}{3}$

<details><summary>查看答案与解析</summary>
**答案:A**。对数似然对 $\mu$、$\sigma^2$ 求偏导得 $\hat{\mu} = \bar{x} = 4$,$\hat{\sigma}^2 = \frac{1}{n}\sum_{i=1}^{n}(x_i - \hat{\mu})^2 = \frac{(2-4)^2 + (4-4)^2 + (6-4)^2}{3} = \frac{8}{3} \approx 2.667$。注意分母是 $n$ 而不是 $n-1$:MLE 的 $\hat{\sigma}^2$ 是**有偏**估计($E[\hat{\sigma}^2] = \frac{n-1}{n}\sigma^2$,系统性偏小),无偏版本 $s^2 = \frac{1}{n-1}\sum(x_i-\bar{x})^2 = 4$,二者关系 $s^2 = \frac{n}{n-1}\hat{\sigma}^2$。选项 B 把无偏估计当成了 MLE(这是最常见的混淆);选项 C 数值对但性质判断错;选项 D 把均值算成了 $(2+4)/2 = 3$(漏了 6)。
</details>

**第 2 题** 设 $X_1, \dots, X_n \sim U(0, \theta)$($\theta > 0$ 未知)。$\theta$ 的极大似然估计是:

A. $\hat{\theta} = \max\{x_i\}$,这是边界解:似然 $1/\theta^n$ 关于 $\theta$ 单调递减,求导无驻点,最大值在可行域下边界取到
B. $\hat{\theta} = \bar{x}$,由得分方程 $\ell'(\theta) = 0$ 解得
C. $\hat{\theta} = 2\bar{x}$,因为均匀分布的期望是 $\theta/2$
D. $\hat{\theta} = \min\{x_i\}$,因为似然关于 $\theta$ 单调递增

<details><summary>查看答案与解析</summary>
**答案:A**。似然函数 $L(\theta) = \frac{1}{\theta^n}\cdot\mathbf{1}\{\max_i x_i < \theta\}$:当 $\theta < \max\{x_i\}$ 时至少一个样本落在区间外,似然为 0(该参数根本不可能产生这批数据);当 $\theta \ge \max\{x_i\}$ 时 $L(\theta) = 1/\theta^n$ 随 $\theta$ 增大而**单调递减**。所以最大值在可行域的下边界 $\hat{\theta} = \max\{x_i\}$ 取到。单调函数没有驻点,得分方程自然无解——这提醒我们:求导只能找到**内部**极值,参数空间的边界必须单独检查。选项 B 误用求导法;选项 C 是**矩估计**的结果($\bar{x} = \theta/2 \Rightarrow \hat{\theta} = 2\bar{x}$),混淆了两种估计方法;选项 D 把单调方向说反。
</details>

**第 3 题** 关于极大似然估计(MLE)的性质,下列说法**正确**的是:

A. MLE 具有一致性、渐近正态性与渐近有效性,且满足不变性($g(\hat{\theta})$ 是 $g(\theta)$ 的 MLE);但它不一定无偏
B. MLE 一定是无偏估计,这是它优于矩估计的原因
C. MLE 一定存在且唯一,并且总能由求导得到
D. MLE 只适用于连续型分布,离散分布无法定义似然函数

<details><summary>查看答案与解析</summary>
**答案:A**。MLE 的四大优良性质:一致性($n\to\infty$ 时依概率收敛到真值)、渐近正态($\sqrt{n}(\hat{\theta}-\theta)$ 渐近 $N(0, 1/I(\theta))$)、渐近有效(方差达到 Cramér-Rao 下界)、不变性(如 $\hat{\lambda}=\bar{x}$ 是泊松参数的 MLE,则 $e^{-\lambda}$ 的 MLE 就是 $e^{-\bar{x}}$)。但它**不一定无偏**:正态的 $\hat{\sigma}^2 = \frac{1}{n}\sum(x_i-\bar{x})^2$ 偏小,$U(0,\theta)$ 的 $\hat{\theta} = \max\{x_i\}$ 也偏小($E[\hat{\theta}] = \frac{n}{n+1}\theta$);MLE 拥有的是**渐近无偏性**。选项 B 把「渐近无偏」当成了「无偏」;选项 C 被 $U(0,\theta)$ 的边界解反例否决(驻点法失效、需数值优化);选项 D 忘了伯努利、泊松等离散分布的 MLE 正是教科书标准内容。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:参数估计是国赛/美赛「数据处理与拟合」类问题的第一步。传染病模型(SIR 的 $\beta, \gamma$)、排队系统($\lambda, \mu$)、寿命可靠性(Weibull 形状参数)都依赖 MLE 或与其等价的负对数似然最小化
- **论文加分点**:①报告估计值的同时给出**标准误**与置信区间——大样本下 $\hat{\theta} \pm 1.96 / \sqrt{n I(\hat{\theta})}$ 近似为 95% 区间;②对多个候选分布做拟合时,列出各模型的**对数似然或 AIC/BIC** 再选优;③说明为何选 MLE 而非矩估计(渐近有效、不变性)
- **工具**:`scipy.stats.fit`(对指定分布做 MLE)、`scipy.optimize.minimize`(自定义似然)、混合模型 EM 用 `sklearn.mixture.GaussianMixture`

## 💻 代码实现

```python
import numpy as np
from scipy.optimize import minimize

# 1. 伯努利 MLE: 10 次抛掷 7 次正面
k, n = 7, 10
print("伯努利 p_hat =", k / n)                      # 0.7

# 2. 正态 MLE(闭式): 样本 (2, 4, 6)
x = np.array([2.0, 4.0, 6.0])
mu_hat = x.mean()
sigma2_hat = ((x - mu_hat) ** 2).mean()
print(f"正态 mu_hat = {mu_hat}, sigma2_hat = {sigma2_hat:.4f}")   # 4, 2.6667

# 3. 指数 MLE: 寿命样本 0.5, 1.0, 1.5
lifetimes = np.array([0.5, 1.0, 1.5])
print("指数 lambda_hat =", 1 / lifetimes.mean())    # 1.0

# 4. 无解析解时: 数值最小化负对数似然 (Gamma 分布)
from scipy.stats import gamma
data = np.random.default_rng(42).gamma(shape=2.0, scale=1.5, size=200)  # 真值 (2, 1.5)

def neg_ll(theta):
    a, s = theta
    return -np.sum(gamma.logpdf(data, a=a, scale=s))

res = minimize(neg_ll, x0=[1.0, 1.0], bounds=[(1e-6, None), (1e-6, None)])
print(f"Gamma 数值 MLE: shape = {res.x[0]:.3f}, scale = {res.x[1]:.3f}")  # 约 (2.14, 1.46),接近真值

# 5. EM 算法: 一维两高斯混合 (E 步: 责任度; M 步: 加权矩估计)
rng = np.random.default_rng(42)
data = np.concatenate([rng.normal(-1.5, 0.6, 600), rng.normal(2.0, 1.0, 400)])
rng.shuffle(data)
pi, mu1, mu2, s1, s2 = 0.5, -0.5, 0.5, 1.0, 1.0          # 任意初始化
for _ in range(200):
    p1 = pi * np.exp(-(data - mu1)**2 / (2*s1)) / np.sqrt(2*np.pi*s1)
    p2 = (1 - pi) * np.exp(-(data - mu2)**2 / (2*s2)) / np.sqrt(2*np.pi*s2)
    g1 = p1 / (p1 + p2 + 1e-300)                          # E 步: 样本属于第 1 类的责任度
    pi = g1.mean()                                        # M 步: 更新混合比例
    mu1 = (g1*data).sum() / g1.sum();  mu2 = ((1-g1)*data).sum() / (1-g1).sum()
    s1 = (g1*(data-mu1)**2).sum() / g1.sum(); s2 = ((1-g1)*(data-mu2)**2).sum() / (1-g1).sum()
print(f"EM 结果: pi = {pi:.2f} (真 0.6), mu = ({mu1:.2f}, {mu2:.2f}) (真 -1.5, 2.0)")
print(f"        sigma = ({np.sqrt(s1):.2f}, {np.sqrt(s2):.2f}) (真 0.6, 1.0)")
```

> EM 迭代 200 次后参数已稳定:$\hat{\pi} \approx 0.60$,均值 $\approx (-1.51, 1.99)$,标准差 $\approx (0.59, 0.98)$,与真值几乎重合。换一组随机种子结果略有波动,但都在真值附近。

## 📚 延伸阅读

- **教材**:茆诗松等《概率论与数理统计教程》(高教社)——「点估计」一章的 MLE 推导最全
- **经典书**:Casella & Berger, *Statistical Inference* —— 对 MLE、Fisher 信息、渐近理论的系统讲解
- **EM 算法**:李航《统计学习方法》第 9 章(高斯混合与 EM);Dempster et al. (1977) 原论文是读一手文献的好素材
- **实战**:scipy 文档 [stats.fit](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fit.html)、sklearn 文档 [GaussianMixture](https://scikit-learn.org/stable/modules/generated/sklearn.mixture.GaussianMixture.html)
- **进阶关联**:学完本单元 → 接着学《贝叶斯推断》(MLE 可视为均匀先验下的 MAP 特例)→ 《线性回归》(最小二乘 = 高斯误差下的 MLE)→ 《蒙特卡洛模拟》(EM 与 MCMC 的接口)

## 🧠 小结

1. MLE 的思想一句话:**选让观测数据出现概率最大的参数**;似然函数 $L(\theta) = \prod f(x_i \mid \theta)$ 把「数据」与「参数」的角色互换
2. 操作三步:写似然 → 取对数 → 求导验证;四大分布(伯努利 / 泊松 / 正态 / 指数)的 MLE 结果要能默写
3. MLE 的性质:一致、渐近正态、渐近有效、变换不变——这是它成为「参数估计第一选择」的理由
4. 警惕边界解($U(0, \theta)$ 的 $\hat{\theta} = \max\{x_i\}$)与有偏性($\hat{\sigma}^2$ 分母是 $n$)
5. 有隐变量时用 EM:E 步算责任度、M 步更新参数,对数似然单调上升
