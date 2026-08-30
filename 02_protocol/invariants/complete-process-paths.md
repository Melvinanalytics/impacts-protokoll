# I4: Complete process paths

## Normative rule

Every Hauptprozess declares its process graph in its canonical `hauptprozess.yaml`. Every reachable node has a declared path to a named end event, a declared wait state, a declared handoff consumer, or a cycle with an explicit continuation or exit condition.

A Hauptprozess declares its entry node and its nodes by stable ID. A node reference resolves within the same Hauptprozess.

## Static validation

The validator applies these checks:

1. **Reachability.** The declared entry node exists. Graph traversal from that entry reaches every declared node. Each `next` target resolves to a declared node.
2. **Gateway completeness.** Every gateway declares one or more routes. Each route declares a condition and a target. Route targets resolve. A gateway with multiple possible outcomes declares the condition for each outcome.
3. **Wait ownership.** Every wait node declares a non-empty trigger and owner. It has exactly one continuation target, which resolves within the same Hauptprozess.
4. **Handoff consumer.** Every handoff declares an artifact reference and a consumer reference. The consumer can receive the declared artifact through a process contract, a named external recipient, or a later process node.
5. **Cycle continuation.** Every reachable cycle declares a continuation condition or an exit condition on a node or route within that cycle. Each declared exit target resolves to a path that reaches a valid outcome.
6. **Named end event.** Every end node declares a non-empty event name. Every terminal graph path reaches such an end node, a valid wait state, a valid handoff, or a valid cycle.

## Valid outcomes

`end` marks a completed outcome. `wait` marks a paused outcome with a declared resumption trigger, owner, and one continuation. `handoff` marks a transfer to a declared consumer. A cycle remains valid when its continuation or exit condition is explicit.

## Validator result

The validator emits a structured issue for each violated condition. Issue codes identify reachability, unresolved targets, incomplete gateways, missing wait triggers, missing handoff consumers, cycles without continuation, and unnamed end events.
