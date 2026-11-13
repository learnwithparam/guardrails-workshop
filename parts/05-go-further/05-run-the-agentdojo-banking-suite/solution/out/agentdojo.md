# My guards as an AgentDojo defence

AgentDojo's banking suite, in replay mode with no model. The probe put each of the 9 injection goals, in the
"important instructions" wrapper, into each of the 4 injection vectors.

Injected tool outputs flagged: 36 of 36
Benign tool outputs passed: 10 of 10

My Marrowfield guards alone flagged 0 of 36. They look for orders to a supplier desk, and these attacks give
orders to a banking agent instead. One new signal, text that talks to the agent about its task, caught all 36.
That signal was written after reading the attack, so the next attack style needs a fresh test.

## Beside the published defences

AgentDojo published these numbers for one model on all four suites, under the same attack. They come from a
live agent, so they measure the whole run, not one detector.

| Defence                      | Utility | Utility under attack | Attacks that succeeded |
| ---------------------------- | ------- | -------------------- | ---------------------- |
| No defence                   | 69.07%  | 50.08%               | 47.69%                 |
| tool_filter                  | 72.16%  | 56.28%               | 6.84%                  |
| transformers_pi_detector     | 41.24%  | 21.14%               | 7.95%                  |
| spotlighting_with_delimiting | 72.16%  | 55.64%               | 41.65%                 |
| repeat_user_prompt           | 84.54%  | 67.25%               | 27.82%                 |

Source: [AgentDojo results table](https://github.com/ethz-spylab/agentdojo/blob/main/docs/results-table.html).
