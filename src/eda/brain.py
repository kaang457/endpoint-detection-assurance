"""The AI agent's 'brain' — what decides the agent's next actions.

This is rule-based on purpose: a pseudo-LLM. The project does not run a model;
it simulates what an application that calls an *external* LLM (and stores a
provider API key on the host) would actually do on the box — read files, make a
real egress to the provider, spawn a tool. A model's reasoning is replaced with
a deterministic plan so the measurement stays reproducible.

The seam is deliberate: a real model-backed brain (one that reads the document
and decides) is a drop-in behind the same `plan()` call later. What must not
change is that the *host effects* are real and the *detection outcome* is what we
measure.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPlan:
    """The actions the agent will take, in order. `compromised` records whether
    the input carried a hidden instruction — the thing a defender cannot read off
    the agent's benign-looking transcript."""

    compromised: bool
    actions: tuple[str, ...]


class RuleBasedBrain:
    """Maps the trust of the agent's input to an action plan. An ordinary
    document yields an ordinary answer; a poisoned one yields the hijack."""

    name = "rule-based (pseudo-LLM)"

    def plan(self, poisoned_input: bool) -> AgentPlan:
        if not poisoned_input:
            return AgentPlan(compromised=False, actions=("use_tool",))
        # Indirect prompt injection: grab the crown jewel and smuggle it out over
        # the trusted model channel, then steal the provider key and beacon it.
        return AgentPlan(
            compromised=True,
            actions=("use_tool", "read_secret", "exfil_over_model", "read_api_key", "exfil_c2"),
        )
