# Guard plan for TODO: the name of your agent

Agent: TODO one line on what your agent does
Owner: TODO who reads this plan and the alerts
Untrusted input: TODO where text from outside reaches the agent, such as an email body or a web page

## Tools

One row for each tool the agent can use. Effect is `read`, `private`, `change`, `money` or `outside`.
Layer is `input`, `tool`, `output` or `result`. Decision is `allow`, `ask` or `deny`.

| Tool | Effect | Layer | Rule | Decision |
| ---- | ------ | ----- | ---- | -------- |
| TODO | TODO   | TODO  | TODO | TODO     |

## Attacks I tried

Try at least three attacks on your agent. Save what happened for each in a file in `evidence/`. The file holds
the attack text and a line that starts `Result:`.

| #   | Attack text | Where it went in | Layer that stopped it | Evidence file |
| --- | ----------- | ---------------- | --------------------- | ------------- |
| 1   | TODO        | TODO             | TODO                  | evidence/TODO |

## Numbers

Attacks tried: TODO
Attacks stopped: TODO
Real tasks tried: TODO
Real tasks still done: TODO

## Known gaps

- TODO one thing your guards do not stop yet, with the attack that shows it
