# ThirdEye

ThirdEye bridges the gap between visible activity and real engineering impact. ThirdEye ingests communication logs (Slack/Teams metadata) and execution data (GitHub, Jira) to compute a per-team, size-stable “True Contribution” score that emphasizes quality over quantity. Signals include: complexity-weighted commits (file churn, commit size), critical-path fixes (bug severity & downstream dependency counts), feature ownership (PR-to-release traceability) and knowledge-sharing (code review depth, docs authored, mentoring events), and context-aware visibility (messages that route work vs. messages that drive decisions). A machine learning model ranks contributors only within their team using percentile/rank-based scoring and robust outlier smoothing so metrics remain comparable as team size varies.

The manager dashboard visualizes Perceived Activity vs. Actual Impact, surfaces an often-overseen “Silent Architects” cohort (high impact, low visibility), and provides drilldowns (evidence per score, timelines, suggested calibration notes for reviews). Lightweight extra features include automated recognition badges (mentor, reliability, critical-fixer, etc.), exportable review summaries, and configurable weight presets for diverse team priorities. ThirdEye requires minimal instrumentation (read-only API connectors, local parsing) and focuses on actionable visibility to ensure that merit and productivity, not noise, drive performance decisions.

## Running frontend

```
npm start
```

## Running backend

```
uvicorn api:app --reload --host 0.0.0.0
```