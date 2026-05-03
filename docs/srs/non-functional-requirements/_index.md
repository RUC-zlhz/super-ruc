# Non-Functional Requirements Index

**Version:** 1.0 | **Created:** 2026-04-13 | **Last Updated:** 2026-04-13

## Summary

- Total NFRs: 5
- Must Have: 5
- Should Have: 0

## NFR Catalog

| ID | Title | Category | Priority | Applies To | File |
|----|-------|----------|----------|------------|------|
| NFR-001 | 敏感数据安全 | Security | Must Have | FR-006, FR-009, FR-012, FR-013, FR-018 | `NFR-001-sensitive-data-security.md` |
| NFR-002 | 审计留存与可追溯性 | Reliability | Must Have | FR-008, FR-012, FR-013, FR-016, FR-017, FR-018 | `NFR-002-audit-retention.md` |
| NFR-003 | 常见操作响应时间 | Performance | Must Have | FR-001, FR-004, FR-007, FR-011, FR-016, FR-017 | `NFR-003-response-time.md` |
| NFR-004 | 事务一致性与数据可靠性 | Reliability | Must Have | FR-005, FR-006, FR-008, FR-009, FR-014, FR-015, FR-017 | `NFR-004-transaction-reliability.md` |
| NFR-005 | 学生与老师的操作易用性 | Usability | Must Have | FR-006, FR-007, FR-008, FR-018 | `NFR-005-operator-usability.md` |

## Coverage Notes

- 安全、审计与一致性构成平台的一期底线能力。
- 响应时间与易用性不是高并发优化问题，而是为了保障低并发场景下的稳定体验与可落地性。
