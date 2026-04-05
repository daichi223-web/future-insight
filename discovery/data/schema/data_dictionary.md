# データ辞書

## students.csv — 生徒マスタ

| カラム | 型 | 説明 |
|--------|-----|------|
| student_id | str | 仮名ID（S001-S500） |
| latent_class | int | 潜在クラス（0-4）※検証用、分析では未使用 |
| course | str | 文系 / 理系 |
| gender | str | M / F |

## item_responses.csv — 設問応答（正誤）

| カラム | 型 | 説明 |
|--------|-----|------|
| student_id | str | FK → students |
| subject | str | math / physics / chemistry / english / japanese |
| item_id | str | 例: math_q01, physics_q15 |
| correct | int | 0=不正解, 1=正解 |

**設問-スキル対応**: 各教科30問、6問ごとにスキル区分
- q01-q06: スキル1（例: math→代数操作）
- q07-q12: スキル2（例: math→幾何推論）
- q13-q18: スキル3（例: math→統計的思考）
- q19-q24: スキル4（例: math→関数理解）
- q25-q30: スキル5（例: math→文章題読解）

## grades.csv — 成績

| カラム | 型 | 説明 |
|--------|-----|------|
| student_id | str | FK → students |
| subject | str | 5教科 |
| term | int | 1-6（3年×2学期） |
| grade | float | 0-100 |

## attendance.csv — 出欠

| カラム | 型 | 説明 |
|--------|-----|------|
| student_id | str | FK → students |
| date | str | YYYY-MM-DD |
| present | int | 0=欠席, 1=出席 |

## mock_exams.csv — 模試

| カラム | 型 | 説明 |
|--------|-----|------|
| student_id | str | FK → students |
| exam_id | str | 例: mock_2024_06 |
| subject | str | 5教科 |
| deviation_score | float | 偏差値（平均50, SD10） |

## entrance_scores.csv — 入試成績

| カラム | 型 | 説明 |
|--------|-----|------|
| student_id | str | FK → students |
| subject | str | 5教科 |
| score | float | 0-100（入試時の素点） |

## ground_truth.json — 検証用（分析では使用しない）

植え込まれた信号の正解データ。分析パイプラインの検証用途のみ。
