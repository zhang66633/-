"""预计算 2023C 数据聚合，加速沙箱执行。

运行一次即可，生成 _precomputed_*.parquet 文件。
沙箱中 pd.read_parquet() 秒级加载，替代 42 秒的 xlsx 读取。
"""
from pathlib import Path
import pandas as pd
import time

td = Path(__file__).parent.parent / "data" / "problems" / "2023C"

print("Loading data...", flush=True)
t0 = time.time()
sales = pd.read_parquet(td / "attachment2_sales.parquet")
products = pd.read_parquet(td / "attachment1_products.parquet")
wholesale = pd.read_parquet(td / "attachment3_wholesale.parquet")
loss = pd.read_parquet(td / "attachment4_loss.parquet")
print(f"  Loaded {len(sales):,} sales rows in {time.time()-t0:.1f}s", flush=True)

# 1. 品类级日聚合
print("1/6 Category daily aggregation...", flush=True)
t0 = time.time()
# 单品编码 -> 分类编码 映射
prod_to_cat = dict(zip(products['product_code'], products['category_code']))
# 单品编码 -> 分类名称 映射
prod_to_catname = dict(zip(products['product_code'], products['category_name']))
sales['category_code'] = sales['product_code'].map(prod_to_cat)

cat_daily = (
    sales.groupby(['category_code', 'sale_date'])
    .agg(volume=('qty_kg', 'sum'), revenue=('revenue', 'sum'), transactions=('qty_kg', 'count'))
    .reset_index()
)
cat_daily['avg_price'] = cat_daily['revenue'] / cat_daily['volume']
cat_daily.to_parquet(td / '_precomputed_category_daily.parquet')
print(f"  {len(cat_daily)} rows, {time.time()-t0:.1f}s", flush=True)

# 2. 品类汇总统计
print("2/6 Category stats...", flush=True)
t0 = time.time()
cat_stats = cat_daily.groupby('category_code').agg(
    avg_daily_volume=('volume', 'mean'),
    std_volume=('volume', 'std'),
    avg_daily_revenue=('revenue', 'mean'),
    avg_price=('avg_price', 'mean'),
    std_price=('avg_price', 'std'),
).reset_index()
cat_stats.to_parquet(td / '_precomputed_category_stats.parquet')
print(f"  {len(cat_stats)} rows, {time.time()-t0:.1f}s", flush=True)

# 3. 单品级日聚合
print("3/6 Product daily aggregation...", flush=True)
t0 = time.time()
prod_daily = (
    sales.groupby(['product_code', 'sale_date'])
    .agg(volume=('qty_kg', 'sum'), revenue=('revenue', 'sum'))
    .reset_index()
)
prod_daily['avg_price'] = prod_daily['revenue'] / prod_daily['volume']
prod_daily.to_parquet(td / '_precomputed_product_daily.parquet')
print(f"  {len(prod_daily)} rows, {time.time()-t0:.1f}s", flush=True)

# 4. 单品汇总统计
print("4/6 Product stats...", flush=True)
t0 = time.time()
prod_stats = prod_daily.groupby('product_code').agg(
    avg_daily_volume=('volume', 'mean'),
    std_volume=('volume', 'std'),
    avg_price=('avg_price', 'mean'),
    std_price=('avg_price', 'std'),
).reset_index()
prod_stats.to_parquet(td / '_precomputed_product_stats.parquet')
print(f"  {len(prod_stats)} rows, {time.time()-t0:.1f}s", flush=True)

# 5. 周内效应
print("5/6 Day-of-week effect...", flush=True)
t0 = time.time()
sales['dow'] = pd.to_datetime(sales['sale_date']).dt.dayofweek  # 0=Mon
dow_effect = (
    sales.groupby('dow')
    .agg(total_volume=('qty_kg', 'sum'), avg_daily_volume=('qty_kg', 'mean'))
    .reset_index()
)
dow_effect.to_parquet(td / '_precomputed_dow.parquet')
print(f"  {len(dow_effect)} rows, {time.time()-t0:.1f}s", flush=True)

# 6. 批发价 + 损耗率
print("6/6 Wholesale & loss...", flush=True)
t0 = time.time()
wp_avg = wholesale.groupby('product_code')['wholesale_price'].mean().reset_index()
wp_avg.to_parquet(td / '_precomputed_wholesale.parquet')
loss.to_parquet(td / '_precomputed_loss.parquet')
print(f"  wholesale {len(wp_avg)}, loss {len(loss)}, {time.time()-t0:.1f}s", flush=True)

# README
(td / 'DATA_README.md').write_text("""# 预计算数据文件

以下文件已从原始 87.8 万行销售数据预计算，沙箱中 pd.read_parquet() 秒级加载：

| 文件 | 用途 | 列 |
|------|------|-----|
| _precomputed_category_daily.parquet | 品类级日聚合 | category_code, sale_date, volume, revenue, transactions, avg_price |
| _precomputed_category_stats.parquet | 品类汇总统计 | category_code, avg_daily_volume, std_volume, avg_daily_revenue, avg_price, std_price |
| _precomputed_product_daily.parquet | 单品级日聚合 | product_code, sale_date, volume, revenue, avg_price |
| _precomputed_product_stats.parquet | 单品汇总统计 | product_code, avg_daily_volume, std_volume, avg_price, std_price |
| _precomputed_dow.parquet | 周内效应 | dow(0=Mon), total_volume, avg_daily_volume |
| _precomputed_wholesale.parquet | 批发价 | product_code, wholesale_price |
| _precomputed_loss.parquet | 损耗率 | category_code, category_name, loss_rate |

原始销售明细（parquet 格式，秒级加载）：
- attachment2_sales.parquet: 87.8万行 (col: sale_date, product_code, qty_kg, unit_price, amount)
- attachment1_products.parquet: 单品分类 (product_code, product_name, category_code, category_name)
- attachment3_wholesale.parquet: 批发价 (date, product_code, wholesale_price)
- attachment4_loss.parquet: 损耗率 (category_code, category_name, loss_rate)

## 使用示例
```python
import pandas as pd
cat_stats = pd.read_parquet('_precomputed_category_stats.parquet')
cat_daily = pd.read_parquet('_precomputed_category_daily.parquet')
prod_stats = pd.read_parquet('_precomputed_product_stats.parquet')
dow = pd.read_parquet('_precomputed_dow.parquet')
wholesale = pd.read_parquet('_precomputed_wholesale.parquet')
```
""", encoding="utf-8")

print(f"\nDone! All precomputed files in {td}")
for f in sorted(td.glob('_precomputed_*')):
    print(f"  {f.name}: {f.stat().st_size/1024:.1f} KB")