from pathlib import Path
import json
import re
import pandas as pd
from lxml import html

BASE = Path(__file__).resolve().parents[1]
paper = BASE / "论文v18-3-3.html"
metrics = json.loads((BASE / "data" / "metrics.json").read_text(encoding="utf-8"))
panel = pd.read_csv(BASE / "data" / "analysis_panel.csv")
root = html.fromstring(paper.read_text(encoding="utf-8"))
text = "".join(root.itertext())

checks = {}
checks["样本数一致"] = len(panel) == metrics["n"] == 2886
checks["品规数一致"] = panel["code"].nunique() == metrics["products"] == 203
checks["处理数一致"] = int(panel["T"].sum()) == metrics["treated"] == 258
checks["结果变量排除处理指标"] = not set(metrics["excluded_from_outcome"]) & set(metrics["outcome_indicators"])
checks["CATE无缺失"] = panel["CATE"].notna().all()
checks["表格数量19"] = len(root.xpath("//table")) == 19
checks["图片数量8"] = len(root.xpath("//img")) == 8
checks["图片文件齐全"] = all((paper.parent / img.get("src")).exists() for img in root.xpath("//img"))
checks["旧结论已清除"] = not re.search(r"60\.6%|23\.6%|-7\.02|-0\.83|-2\.34|5%[～~]8%|3%[～~]5%|SHAP", text)
checks["摘要四要素"] = all(k in text[:6000] for k in ["【目的】", "【方法】", "【结果】", "【结论】"])
checks["证据边界披露"] = "处理前负对照" in text and "探索性排序" in text
checks["固定比例已取消"] = "不提供固定百分比缩投剂量" in text
checks["作者占位符已提示"] = "请填写真实作者姓名" in text

failed = [k for k, v in checks.items() if not v]
checks = {k: bool(v) for k, v in checks.items()}
report = {"checks": checks, "failed": failed, "status": "PASS" if not failed else "FAIL"}
(BASE / "data" / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
