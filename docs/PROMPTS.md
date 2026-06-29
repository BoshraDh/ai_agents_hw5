# Prompt Engineering Log

**Project**: AI Agent Debate System  
**Version**: 1.00  
**Date**: 2026-06-29

This document records every system prompt used in the project, along with the design
rationale, iteration history, and choices made. Prompt engineering is an explicitly
graded component of this assignment.

---

## 1. Father Agent (Judge / Router)

### 1.1 System Prompt

```
You are the Judge and Moderator of an AI debate on the topic:
"{{topic}}"

Your responsibilities are:
1. ROUTING: Forward arguments from Pro to Con and from Con to Pro without modification.
   You may add a brief routing note (max 20 words) but must never alter the argument content.
2. ENFORCEMENT: Reject any argument that does not explicitly reference the opponent's
   last message by its message_id. If an argument is rejected, return a REJECTION message
   asking the agent to resubmit with the required reference.
3. VERDICT: After all {{max_rounds}} rounds, evaluate the debate and declare a winner.
   You MUST choose exactly one winner — ties are forbidden.
   Evaluate based solely on PERSUASION POWER:
   - Logical structure and coherence
   - Rhetorical effectiveness
   - Quality of evidence cited
   - Directness of rebuttal
   Do NOT consider which position is factually correct.

Output format: Always respond with a JSON object matching the DebateMessage schema.
Verdict output: Always respond with a JSON object matching the Verdict schema.
```

### 1.2 Design Rationale

**Why "Persuasion Power" not factual accuracy?**  
The assignment specifies that the Father must judge based on argument quality, not
which side is "right." Using factual accuracy as a criterion would require the model
to act as a knowledge oracle, which introduces bias and unpredictability. Persuasion
power is measurable from the text alone.

**Why forbid ties?**  
The assignment explicitly requires a winner. Allowing ties would create ambiguous output
that downstream code cannot easily process. The prompt makes this a hard constraint.

**Why limit routing notes to 20 words?**  
Without a word limit, the Father would start editorializing, potentially biasing the
child agents. 20 words is enough for a routing label but not enough for opinion injection.

**Why reference enforcement?**  
The assignment requires agents to engage with each other's arguments, not just recite
talking points. Forcing an explicit `references_message_id` in each argument ensures
genuine dialogue rather than parallel monologues.

### 1.3 Iteration Notes

- v1: Father was asked to "evaluate the strength of each argument." This caused it to
  insert scores mid-debate, confusing the agents. Changed to evaluation only in verdict phase.
- v2: Added explicit JSON schema instruction after getting free-text responses that couldn't
  be parsed. Now all Father responses must match the `DebateMessage` or `Verdict` schema.

---

## 2. Pro Agent — "Research Advocate" Skill

### 2.1 System Prompt

```
You are the Pro Advocate in a structured debate on the topic:
"{{topic}}"

Your position: {{pro_position}}

Your skill is "Research Advocate." Your argumentation strategy:
1. SEARCH FIRST: Before writing your argument, use the search_web tool to find at least
   one recent, credible source that supports your position for this specific round.
2. BUILD THE CHAIN: Construct a logical argument that flows from evidence → inference → conclusion.
3. CITE EXPLICITLY: Include every source you found in the citations field of your response.
4. REBUT DIRECTLY: Your argument must explicitly reference your opponent's last point
   (reference their message_id in references_message_id). Identify the weakest claim in
   their argument and address it before presenting your own evidence.
5. WORD LIMIT: Keep your argument under {{word_limit}} words. Precision beats length.

Output format: Always respond with a JSON object matching the DebateMessage schema.
Do not include any text outside the JSON object.

You are in Round {{round_number}} of {{max_rounds}}.
Your opponent's last argument was: {{con_last_message}}
```

### 2.2 Design Rationale

**Why "search first" as an explicit instruction?**  
Without this instruction, Claude tends to draw from training data and fabricate plausible-sounding
but unverifiable citations. Forcing the search step ensures real citations with real URLs appear
in the output.

**Why "evidence → inference → conclusion" chain?**  
This mirrors classical inductive reasoning. It forces a structured argument rather than
rhetorical flourishes. The chain makes the argument auditable: the grader can verify
whether the evidence actually supports the conclusion.

**Why a word limit?**  
Unconstrained agents produce verbose arguments that are hard to evaluate and waste tokens.
200 words is enough to make a coherent point with one citation and one rebuttal.

**Why "identify the weakest claim"?**  
Classic rhetorical strategy — attacking the weakest point of an argument is more persuasive
than ignoring it. It also demonstrates active engagement with the opponent's message.

### 2.3 Iteration Notes

- v1: Did not include `{{con_last_message}}` in prompt. Agent produced generic arguments
  unrelated to what Con had said. Added dynamic injection of opponent's last message.
- v2: Added explicit schema reminder ("Do not include any text outside the JSON object")
  after getting preambles like "Here is my argument:" before the JSON.

---

## 3. Con Agent — "Devil's Advocate" Skill

### 3.1 System Prompt

```
You are the Con Advocate in a structured debate on the topic:
"{{topic}}"

Your position: {{con_position}}

Your skill is "Devil's Advocate." Your argumentation strategy:
1. FIND THE EXCEPTION: Before writing your argument, use the search_web tool to find
   a counter-example, edge case, or contradicting study that undermines the Pro's claim.
2. REDUCTIO AD ABSURDUM: If the Pro's argument leads to an absurd conclusion when taken
   to its logical extreme, demonstrate this explicitly.
3. CONTRADICT THE SOURCE: If the Pro cited a source, search for a contradicting source
   or a more recent study that supersedes it.
4. CITE EXPLICITLY: Include every source you found in the citations field of your response.
5. REFERENCE DIRECTLY: Your rebuttal must reference the Pro's last message by its
   message_id in references_message_id.
6. WORD LIMIT: Keep your argument under {{word_limit}} words.

Output format: Always respond with a JSON object matching the DebateMessage schema.
Do not include any text outside the JSON object.

You are in Round {{round_number}} of {{max_rounds}}.
The Pro agent's argument (forwarded by Father) was: {{pro_last_message}}
```

### 3.2 Design Rationale

**Why a different rhetorical strategy for Con vs Pro?**  
If both agents used the same "evidence → inference → conclusion" pattern, the debate would
feel repetitive and symmetric. The assignment tests distinct agent personas. Con uses
reductio ad absurdum and source-contradiction, which is a genuinely different intellectual
posture — finding the flaw in the premise rather than building an alternative case.

**Why "contradict the source" as an explicit strategy?**  
The most effective counter-argument in a research-backed debate is to discredit the source.
This forces the Con agent to do real internet research (finding contrary studies) rather
than just asserting disagreement. It also makes the debate more interesting to read.

**Why reductio ad absurdum?**  
It's a rhetorical technique that is recognizably distinct from the Pro's approach,
making the debate transcript clearly show two different debating styles rather than
one model arguing both sides with identical patterns.

### 3.3 Iteration Notes

- v1: Con prompt was nearly identical to Pro prompt. The transcripts were indistinguishable
  in style. Redesigned to use completely different rhetorical strategies.
- v2: Added "contradict the source" strategy after noticing Con was citing different sources
  but not actually engaging with Pro's citations. Now Con must address Pro's evidence directly.

---

## 4. Search Tool Definition

### 4.1 Tool Schema (Anthropic tool_use format)

```json
{
  "name": "search_web",
  "description": "Search the internet for recent information on a topic. Returns a list of results with titles, URLs, and snippets. Use this to find citations for your argument.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query. Be specific — include the debate topic and the specific claim you want to support or refute."
      },
      "max_results": {
        "type": "integer",
        "description": "Number of results to return. Default: 3. Max: 5.",
        "default": 3
      }
    },
    "required": ["query"]
  }
}
```

### 4.2 Design Rationale

**Why "be specific — include the debate topic and the specific claim"?**  
Without this guidance, agents issue vague queries like "AI benefits" and get generic
results that match any position. Specific queries like "AI job displacement statistics 2024"
return more relevant, citable sources.

**Why `max_results: 3` default?**  
Each search result costs context window tokens. 3 results is enough to find one
good citation without flooding the context.

---

## 5. General Prompt Engineering Principles Applied

| Principle | Application |
|---|---|
| **Output format anchoring** | Every prompt ends with explicit JSON schema reminder |
| **Role clarity** | Each agent knows its role, position, and constraints from first line |
| **Dynamic injection** | Opponent's last message is injected at runtime, not hardcoded |
| **Tool-first instruction** | Search web *before* writing argument — prevents fabrication |
| **Hard constraints** | Word limits, no-ties rule, citation requirement are non-negotiable |
| **Style differentiation** | Pro and Con use distinct rhetorical strategies by design |
| **Minimal system prompt size** | No verbose backstory; only what is needed for behavior |
