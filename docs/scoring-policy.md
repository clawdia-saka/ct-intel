# CTIE Importance Scoring Policy

## 設計思想
- LLMに重要度判断を丸投げしない
- まずsourceと内容をルールで採点
- LLMは整形と日本語化
- SNSノイズは主役にしない
- 重要論点が少ない日は少ないと返す

---

## スコア項目

### A. Source Reliability（0〜100）
| source type | base score |
|-------------|-----------|
| official | 95 |
| market | 90 |
| owned | 75 |
| signal | 50 |

補正: 公式URL +5 / 署名付きレポート +5 / 不明二次ソース -15

### B. Market Impact（0〜100）
- BTC/ETH/ETF/規制/セキュリティ事故: 80〜95
- SOL/major L2/infra/stablecoin: 65〜85
- 中小トークン単体: 30〜60
- ローカルイベント/マイナー提携: 20〜40
- 複数銘柄波及: +10 / 単独小型: -15

### C. Novelty（0〜100）
- 24h以内に同一論点なし: 80
- 類似あるが新情報: 55
- 焼き直し: 20

### D. Japan Relevance（0〜100）
- 日本の規制/取引所/企業/円建て: 80〜95
- 日本語圏で需要高い主要テーマ: 50〜75
- 海外ローカル接点薄い: 10〜40

### E. Time Sensitivity（0〜100）
- 24h以内に判断価値: 80〜95
- 今週中に重要: 50〜70
- 急ぎではない: 20〜40

### F. Cross-source Confirmation（0〜100）
- official + market/owned: 90
- official単独: 75
- owned単独: 60
- signal単独: 25

---

## ペナルティ

### Duplication Penalty
- 同一URL: -100（除外）
- 類似タイトル/同論点再掲: -20〜-40

### Hype Penalty
- 「爆上げ」「moon」「100x」「確実」等: -10〜-30

### Weak Evidence Penalty
- SNS一件のみ: -30
- 一次ソース不明: -20
- 公開時刻不明/出典不完全: -10

---

## 最終スコア計算

```
FINAL_SCORE =
  0.25 * source_reliability +
  0.25 * market_impact +
  0.15 * novelty +
  0.15 * japan_relevance +
  0.10 * time_sensitivity +
  0.10 * cross_source_confirmation
  - duplication_penalty
  - hype_penalty
  - weak_evidence_penalty
```

---

## 優先度閾値

| score | priority |
|-------|----------|
| 80+ | P1 |
| 60〜79 | P2 |
| 40〜59 | P3 |
| 39以下 | archive |

---

## Quiet Day判定
以下すべてを満たす場合:
- P1が0件
- P2が2件未満
- major asset/regulation/security incidentがない

→ Morning Brief冒頭に「今日は新規の大型材料は限定的です」と入れる
