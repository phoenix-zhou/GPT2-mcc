# Security and Risk Review / 安全与风险审计

**Review date / 审计日期:** 2026-08-13
**Scope / 范围:** current tracked application, agent, retrieval, evaluation,
Skills, CI, templates, and legacy data-processing code. A credential-pattern
scan of reachable Git history was also performed. The local environment was
upgraded before the final dependency scan.

This is an engineering review, not a penetration test, clinical validation,
privacy certification, or legal opinion.

## Executive result / 结论

The review removed unsafe generated artifacts, constrained legacy Pickle
loading, hardened the web boundary, closed evidence-source impersonation and
agent-marker confusion paths, reduced sensitive error persistence, and pinned
CI dependencies. No credential-shaped secret was found in the current tracked
tree or the history pattern scan. The locally installed Python environment
reported no known dependency vulnerabilities through `pip-audit` at review
time.

本次审计移除了不安全的生成产物，限制了历史 Pickle 加载，强化了 Web 边界，修复
证据来源冒充和 Agent 标记混淆路径，减少敏感异常持久化，并固定 CI Action 版本。
当前受跟踪文件和 Git 历史模式扫描中未发现密钥形态的凭据；审计时本地安装环境的
`pip-audit` 未报告已知依赖漏洞。

## Findings and disposition / 发现与处置

| Severity | Finding | Disposition |
|---|---|---|
| High | Legacy training used unrestricted `pickle.load`, enabling code execution from a malicious dataset | Replaced with a restricted unpickler that rejects globals/classes and enforces file, sequence, length, and token bounds; malicious-payload regression added |
| High | Legacy training text contained contact-shaped identifiers and could contain additional indirect identifiers; generated Pickles duplicated the content | Raw legacy text and Pickles removed from the current tree; local data directory ignored. Earlier Git history/upstream copies may remain and require a separately approved history-rewrite decision |
| Medium | POST forms had no CSRF validation and model calls had no abuse throttle | Signed-session CSRF tokens, request-size cap, and bounded thread-safe in-memory rate limiter added |
| Medium | A record could claim an approved `source_id` while linking to an unrelated HTTPS host | Record URL host must now match the approved source homepage host or a subdomain; issuer, organization, jurisdiction, and source type are bound too |
| Medium | Nested agent role markers could blur planner/responder boundaries | Top-level response marker is enforced; action/reason pairs are validated together; nested markers are treated as untrusted user content |
| Medium | Provider/runtime exception text could be logged or persisted into evaluation artifacts | Server logging and evaluation captures now retain only controlled error classes/messages |
| Medium | Hosted-model example referenced an invalid default model ID | Default and examples changed to the documented `gpt-5.6-terra` model |
| Medium | Local model used a mutable repository head, and legacy GPT-2 could load executable Pickle-based weights | Default Qwen revision pinned; GPT-2 removed from web providers and restricted to local Safetensors checkpoints |
| Medium | GitHub Actions used mutable major tags and retained checkout credentials | Actions pinned to reviewed commit SHAs; checkout credential persistence disabled; CI adds `pip-audit` |
| Low | Legacy CLI could write raw conversation samples by default | Sample logging is opt-in and disabled by default; documentation forbids sensitive data |
| Legal / provenance | Upstream declares no open-source license; legacy dataset provenance and reuse rights are unresolved | Prominent README warning added. Technical changes cannot resolve permission or licensing |

## Threat model and trust boundaries / 威胁模型与信任边界

- Browser input, planner output, model output, evidence files, legacy datasets,
  and provider exceptions are untrusted.
- The current agent has one read-only evidence tool and no shell, network-write,
  financial, messaging, or user-account side effect. Prompt injection can still
  affect generated text, but its operational blast radius is deliberately small.
- The Flask session cookie stores an opaque conversation identifier and CSRF
  token; conversation text remains in bounded process memory.
- Emergency routing is deterministic and precedes model invocation. It can
  still miss paraphrases or over-route benign input.
- Evidence governance verifies metadata and integrity, not clinical truth.

## Residual risks / 剩余风险

1. **Not production-ready.** No user identity, authorization, distributed rate
   limiter, durable encrypted session store, WAF, centralized audit trail,
   incident response integration, or compliance program exists.
2. **Safety remains incomplete.** Keyword/phrase routing has false-positive and
   false-negative risk and is not a medical device.
3. **Evidence is thin.** The corpus contains twelve project-authored summaries
   that have not been reviewed by clinicians.
4. **Evaluation is development-set evidence.** The cases are small,
   project-reviewed, and not independent; reported metrics may be optimistic.
5. **Semantic groundedness is not fully measured.** Valid citation IDs do not
   prove every generated claim is supported by the cited page.
6. **Prompt injection is reduced, not solved.** Models may still follow hostile
   prose; bounded tools prevent most external side effects but not misleading text.
7. **History and upstream retention.** Raw legacy datasets are absent from the
   current tree. Earlier commits and upstream repositories may retain them.
8. **Legal uncertainty remains.** Missing upstream license and unresolved data
   provenance block a confident redistribution/commercial-use claim.

## Verification / 验证

```bash
python -m pip install -e '.[dev]'
python scripts/validate_knowledge.py
pytest
python -m pip_audit . --progress-spinner off
```

Security-sensitive regression coverage includes CSRF, request-size and rate
limits, production configuration fail-closed behavior, response headers,
planner marker injection, action/reason mismatch, evidence source binding,
metadata/freshness validation, privacy-safe error capture, and malicious Pickle
rejection.

## Release recommendation / 发布建议

Suitable for a local portfolio demonstration after tests pass. Do not expose
the Flask development server to the public internet. Before external multi-user
deployment, add authentication and authorization, a production WSGI server and
reverse proxy, distributed abuse controls, encrypted persistence and retention
policy, structured redacted observability, independent safety/evaluation review,
and explicit legal permission for reused code and data.

在全部测试通过后，可用于本地作品集演示；不可直接把 Flask 开发服务器暴露到公网。
公网多用户部署之前，需要补充认证授权、生产 WSGI 与反向代理、分布式滥用防护、
加密持久化与保留策略、脱敏可观测性、独立安全/评测复核，以及代码和数据的明确授权。
