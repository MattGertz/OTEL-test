# Measurement Results

**Generated**: 2026-04-07 19:30:36 UTC
**Measurers run**: 38

## Summary

| Measurer | Kind | Items | Completed | Failed | Skipped | Avg Raw Score | Min | Max | Scale |
|----------|------|------:|----------:|-------:|--------:|--------------:|----:|----:|-------|
| async-exception-handling | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | [0,1] ▲ |
| atif-trajectory-cache-efficiency | Deterministic | 1 | 1 | 0 | 0 | 0.86 | 0.86 | 0.86 | 0–1 ▲ |
| atif-trajectory-cached-tokens | Deterministic | 1 | 1 | 0 | 0 | 1622990.00 | 1622990.00 | 1622990.00 | 0–∞ ▲ |
| atif-trajectory-input-tokens | Deterministic | 1 | 1 | 0 | 0 | 1896734.00 | 1896734.00 | 1896734.00 | 0–∞ ▼ |
| atif-trajectory-output-tokens | Deterministic | 1 | 1 | 0 | 0 | 14860.00 | 14860.00 | 14860.00 | 0–∞ ▼ |
| atif-trajectory-read-write-ratio | Deterministic | 1 | 1 | 0 | 0 | 0.50 | 0.50 | 0.50 | 0–∞ ▼ |
| atif-trajectory-step-count | Deterministic | 1 | 1 | 0 | 0 | 27.00 | 27.00 | 27.00 | 0–∞ ▼ |
| atif-trajectory-tool-call-count | Deterministic | 1 | 1 | 0 | 0 | 27.00 | 27.00 | 27.00 | 0–∞ ▼ |
| atif-trajectory-total-cost | Deterministic | 1 | 1 | 0 | 0 | 78.00 | 78.00 | 78.00 | 0–∞ ▼ |
| atif-trajectory-wasted-edits | Deterministic | 1 | 1 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0–∞ ▼ |
| code-duplication | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | 0–1 ▲ |
| comment-quality-no-roslyn | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | 0–1 ▲ |
| comment-quality-with-roslyn | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | 0–1 ▲ |
| cyclomatic-complexity | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 1–100 ▼ |
| cyclomatic-complexity | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | 1–100 ▼ |
| empty-catch-blocks | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▼ |
| magic-numbers | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▼ |
| method-length | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▼ |
| msbench-trajectory-cache-efficiency | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-cached-input-tokens | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-input-tokens | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-model-vs-tool-duration | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-output-tokens | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-read-write-ratio | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-tool-call-count | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-tool-success-ratio | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-turn-count | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| msbench-trajectory-wasted-edits | Deterministic | 0 | 0 | 0 | 0 | — | — | — | — |
| naming-conventions | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–1 ▲ |
| nesting-depth | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▼ |
| parameter-count | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▼ |
| performance | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | 0–1 ▲ |
| public-api-ratio | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–1 ▼ |
| test-to-production-ratio | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▲ |
| type-size | Deterministic | 1 | 0 | 0 | 1 | — | — | — | 0–∞ ▼ |
| usings-sorted | Deterministic | 1 | 0 | 0 | 1 | — | — | — | [0,1] ▲ |
| usings-sorted | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | [0,1] ▲ |
| winforms-designer-errors | ModelBacked | 1 | 0 | 0 | 1 | — | — | — | [0,1] ▲ |

## Details

### async-exception-handling (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### atif-trajectory-cache-efficiency (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **0.86** | 2ms
  > 1,622,990/1,896,734 prompt tokens cached (85.6%).

### atif-trajectory-cached-tokens (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **1622990.00** | 0ms
  > 1,622,990 cached tokens.

### atif-trajectory-input-tokens (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **1896734.00** | 0ms
  > 1,896,734 prompt tokens.

### atif-trajectory-output-tokens (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **14860.00** | 0ms
  > 14,860 completion tokens.

### atif-trajectory-read-write-ratio (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **0.50** | 1ms
  > 2 reads / 4 writes = 0.50.

### atif-trajectory-step-count (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **27.00** | 0ms
  > 27 agent step(s).

### atif-trajectory-tool-call-count (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **27.00** | 1ms
  > 27 tool call(s).

### atif-trajectory-total-cost (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **78.00** | 1ms
  > $78.0000 USD.

### atif-trajectory-wasted-edits (Deterministic)

- [Completed] AtifTrajectory: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json (30 steps) | Value: **0.00** | 2ms
  > 0 wasted edit(s) out of 1 total edit(s).

### code-duplication (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### comment-quality-no-roslyn (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### comment-quality-with-roslyn (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### cyclomatic-complexity (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### cyclomatic-complexity (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### empty-catch-blocks (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### magic-numbers (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### method-length (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### msbench-trajectory-cache-efficiency (Deterministic)


### msbench-trajectory-cached-input-tokens (Deterministic)


### msbench-trajectory-input-tokens (Deterministic)


### msbench-trajectory-model-vs-tool-duration (Deterministic)


### msbench-trajectory-output-tokens (Deterministic)


### msbench-trajectory-read-write-ratio (Deterministic)


### msbench-trajectory-tool-call-count (Deterministic)


### msbench-trajectory-tool-success-ratio (Deterministic)


### msbench-trajectory-turn-count (Deterministic)


### msbench-trajectory-wasted-edits (Deterministic)


### naming-conventions (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### nesting-depth (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### parameter-count (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### performance (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### public-api-ratio (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### test-to-production-ratio (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### type-size (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### usings-sorted (Deterministic)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### usings-sorted (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

### winforms-designer-errors (ModelBacked)

- [Skipped] File: C:\Users\mattge\source\repos\scratch\watson-output-vscode\48de0c87\48de0c87.atif.json | Value: — | 0ms
  > File does not match patterns: *.cs

