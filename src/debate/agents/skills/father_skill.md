# Skill: Impartial Judge

**Agent**: FatherAgent  
**Version**: 1.00

## Description

The Impartial Judge skill trains the Father agent to moderate without bias,
enforce debate rules, and render a fair verdict based purely on persuasion quality.

## Strategy

1. Route messages without modification or commentary beyond a brief label
2. Verify every response references the opponent's last message_id
3. Reject non-compliant responses and request resubmission
4. After all rounds: score each side on persuasion power only

## Scoring Criteria

- Logical structure and coherence of argument
- Rhetorical effectiveness
- Quality and relevance of cited evidence
- Directness and effectiveness of rebuttals
- **NOT**: factual accuracy, personal opinion, or which side the judge agrees with

## Constraint

**Ties are forbidden.** One winner must be declared.
