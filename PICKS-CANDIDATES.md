# Watch and read candidates

For the page pass. Cut each part to 4 to 6 picks, with at least 2 videos, then delete this file.

How to read the lists. "Bar" is why the pick passes section 5 of STANDARD-v2.md: made by the person or team who
made or runs the method, about the idea and not a product launch, and not a listicle, SEO site, content farm or
paywall. The links were written without a live check, so the nightly link job must confirm each one. Rows marked
"confirm" need their exact title or video checked first. Where a pick is a video, it says so.

## Orientation

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | OWASP Top 10 for LLM Applications | OWASP GenAI Security Project, 2025 | read | The standards body for the list the course is built on. Evergreen risk names (LLM01 to LLM10). |
| 2 | Prompt injection: what's the worst that can happen? | Simon Willison, 2023 | read | Willison named the attack and has tracked it since. A first-hand walk through the agent case. |
| 3 | The lethal trifecta for AI agents | Simon Willison, 2025 | read | The author of the idea. Explains private data, untrusted text and outside action in plain words. |
| 4 | Not what you've signed up for: compromising real-world LLM-integrated applications with indirect prompt injection (arXiv 2302.12173) | Greshake et al., 2023 | read | The original paper that named indirect injection. |
| 5 | Building effective agents | Anthropic, 2024 | read | An engineering blog from a team that runs agents. About patterns, not a launch. |
| 6 | Intro to Large Language Models (the LLM security section) | Andrej Karpathy, 2023 | video | A widely used talk from a researcher who built these systems. Covers prompt injection and poisoning in one sitting. |
| 7 | Agents Rule of Two | Meta AI security team, 2025 | read | The team that runs Llama agents. A short rule a beginner can hold in mind. |
| 8 | AgentDojo: a dynamic environment to evaluate prompt injection attacks and defenses for LLM agents (arXiv 2406.13352) | Debenedetti et al., 2024 | read | The benchmark the course's later steps point at, written by its makers. |
| 9 | Adversarial machine learning: a taxonomy and terminology of attacks and mitigations (NIST AI 100-2) | NIST, 2025 | read | A government standards body. Gives the shared words. Confirm the edition. |
| 10 | Prompt injection is not SQL injection | UK National Cyber Security Centre, 2025 | read | The national cyber agency. Explains why the old fix does not carry over. Confirm the title. |

## Break the desk

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | Lessons from red teaming 100 generative AI products (arXiv 2501.07238) | Microsoft AI Red Team, 2025 | read | The team that runs the method in production. Plain lessons for writing an attack set. |
| 2 | Red Teaming Language Models with Language Models (arXiv 2202.03286) | Perez et al., DeepMind, 2022 | read | The original paper on generating attacks with a model. Backs the attack-set step. |
| 3 | Red Teaming Language Models to Reduce Harms (arXiv 2209.07858) | Ganguli et al., Anthropic, 2022 | read | The original paper on human red teams and how to score them. |
| 4 | Ignore This Title and HackAPrompt (arXiv 2311.16119) | Schulhoff et al., 2023 | read | Authors ran the largest prompt hacking contest and published its data. Shows how attackers think. |
| 5 | garak: a framework for security probing large language models (arXiv 2406.11036) | Derczynski et al., NVIDIA, 2024 | read | The makers of the scanner. Shows what probes exist. |
| 6 | PyRIT documentation | Microsoft AI Red Team, ongoing | read | Official docs of the tool the team uses. Shows the loop of attack, score, repeat. |
| 7 | Red teaming guide (promptfoo docs) | promptfoo maintainers, ongoing | read | Official docs of the tool the go-further part uses. Confirm it stays about method. |
| 8 | Gandalf, the prompt injection game | Lakera, 2023 | play | A company that runs injection defence in production. Play it before you write attacks. Not a read, so treat it as a hands-on pick. |
| 9 | Hacking AI agents (conference talks) | Johann Rehberger, 2024 to 2025 | video | A researcher who found and disclosed these bugs. Confirm which talk, and its length. |
| 10 | Living off Microsoft Copilot (Black Hat talk) | Michael Bargury, 2024 | video | A researcher showing real injection paths on a shipped product. Confirm the title. |

## Guard what comes in

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | Defending against indirect prompt injection attacks with spotlighting (arXiv 2403.14720) | Hines et al., Microsoft, 2024 | read | The team that made the method. Backs the quarantine and labelling steps. |
| 2 | The instruction hierarchy (arXiv 2404.13208) | Wallace et al., OpenAI, 2024 | read | The lab that trains the models. Why text from outside must rank lower. |
| 3 | The Dual LLM pattern for building AI assistants that can resist prompt injection | Simon Willison, 2023 | read | The author of the quarantined reader idea the course uses. |
| 4 | Design patterns for securing LLM agents against prompt injections (arXiv 2506.08837) | Beurer-Kellner et al., 2025 | read | A joint paper from teams that run agents. Names the patterns in the course. |
| 5 | Defeating prompt injections by design (CaMeL, arXiv 2503.18813) | Debenedetti et al., Google DeepMind, 2025 | read | The method's authors. Shows why a detector alone is not the promise. |
| 6 | Llama Prompt Guard 2 model card | Meta, 2025 | read | The maker of the detector. Gives its numbers and limits. |
| 7 | PoisonedRAG (arXiv 2402.07867) | Zou et al., 2024 | read | The original attack paper for poisoned retrieval. Backs the new poisoned notes step. |
| 8 | Poisoning web-scale training datasets is practical (arXiv 2302.10149) | Carlini et al., 2023 | read | The authors of the attack. Shows that poison needs little effort. |
| 9 | ChatGPT: hacking memories with prompt injection | Johann Rehberger, 2024 | read | The researcher who disclosed the memory attack. The example behind the notes step. |
| 10 | OWASP LLM04 data and model poisoning, and LLM08 vector and embedding weaknesses | OWASP GenAI Security Project, 2025 | read | The standards pages the step cites. Short and stable. |
| 11 | EchoLeak (arXiv 2509.10540) | Aim Security researchers, 2025 | read | First-hand write-up of the attack the part's assignment cites. Confirm the title. |

## Guard what the desk does

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | OWASP LLM06 excessive agency, and LLM10 unbounded consumption | OWASP GenAI Security Project, 2025 | read | The standards pages behind the allow list and the caps. |
| 2 | The protection of information in computer systems | Saltzer and Schroeder, 1975 | read | The original paper on least privilege. Evergreen. Long, so read the principles section only. |
| 3 | Agents Rule of Two | Meta AI security team, 2025 | read | The rule the trifecta step enforces. |
| 4 | The lethal trifecta for AI agents | Simon Willison, 2025 | read | The idea the step is named for. |
| 5 | Design patterns for securing LLM agents against prompt injections (arXiv 2506.08837) | Beurer-Kellner et al., 2025 | read | Plan then execute and action selection, the patterns behind the go-further plan step. |
| 6 | Making Claude Code more secure and autonomous with sandboxing | Anthropic engineering, 2025 | read | A team that ships a permissioned agent. Shows deny rules and approval in practice. Confirm the title. |
| 7 | An introduction to Google's approach to AI agent security | Google, 2025 | read | A large operator's view of limits on agent power. Confirm the title. |
| 8 | Building effective agents (human in the loop, stopping conditions) | Anthropic, 2024 | read | Backs the ask step and the loop cap. |
| 9 | AgentDojo (arXiv 2406.13352) | Debenedetti et al., 2024 | read | Shows utility and security measured together, as the course does. |
| 10 | Karpathy on agents and the human in the loop (conference talk) | Andrej Karpathy, 2025 | video | A builder explaining why a person should approve risky steps. Confirm which talk. |

## Guard what goes out

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | OWASP LLM05 improper output handling, and LLM07 system prompt leakage | OWASP GenAI Security Project, 2025 | read | The standards pages behind the reply step and the new leak rule. |
| 2 | Ignore previous prompt: attack techniques for language models (arXiv 2211.09527) | Perez and Ribeiro, 2022 | read | The original paper on prompt leaking. |
| 3 | Bing Chat data exfiltration: poc and fix | Johann Rehberger, 2023 | read | The researcher's first-hand write-up of the link and image leak the step blocks. |
| 4 | Markdown image exfiltration (posts and tag) | Simon Willison, 2023 to 2025 | read | A maintained record of real cases across vendors. Confirm a single post. |
| 5 | Constitutional classifiers (arXiv 2501.18837) | Anthropic, 2025 | read | A team that runs output and input classifiers in production. Shows cost and false alarms. |
| 6 | Llama Guard: LLM-based input-output safeguard (arXiv 2312.06674) | Inan et al., Meta, 2023 | read | The makers of the model. Backs scoring a classifier on your own set. |
| 7 | NeMo Guardrails (arXiv 2310.10501) | Rebedea et al., NVIDIA, 2023 | read | The makers of the rails the course uses. |
| 8 | Monitoring distributed systems | Google SRE book, 2016 | read | The team that runs the method. Backs logging every decision and a quiet alert. |
| 9 | OpenTelemetry semantic conventions for generative AI | OpenTelemetry project, ongoing | read | The project's own spec for what to log per model call. Confirm it is stable. |
| 10 | Mitigate jailbreaks and prompt injections | Anthropic docs, ongoing | read | Official docs on screening outputs. Keep only if still current. |

## Go further

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | AgentDojo (arXiv 2406.13352) | Debenedetti et al., 2024 | read | Backs the banking suite step. |
| 2 | Defeating prompt injections by design (CaMeL, arXiv 2503.18813) | Debenedetti et al., 2025 | read | Backs the plan-first and untrusted payee steps. |
| 3 | LlamaFirewall (arXiv 2505.03574) | Meta, 2025 | read | The makers of a layered guard framework. Confirm the title. |
| 4 | Llama Guard (arXiv 2312.06674) | Inan et al., Meta, 2023 | read | Backs the Llama Guard scoring step. |
| 5 | NeMo Guardrails (arXiv 2310.10501) | Rebedea et al., NVIDIA, 2023 | read | Backs the framework swap step. |
| 6 | InjecAgent (arXiv 2403.02691) | Zhan et al., 2024 | read | A second benchmark by its authors. Shows a different way to score. |
| 7 | The attacker moves second: stronger adaptive attacks bypass defenses | Nasr, Carlini and others, 2025 | read | Authors of the study. Honest limits of every detector. Confirm the title and arXiv number. |
| 8 | Canarying releases (SRE workbook) | Google SRE, 2018 | read | The team that runs the method. Backs shadow mode for a new guard. |
| 9 | Red teaming guide (promptfoo docs) | promptfoo maintainers, ongoing | read | Backs the attack generation step. |
| 10 | NeMo Guardrails getting started (video from the NVIDIA developer channel) | NVIDIA, 2023 to 2024 | video | The maker walks through a rail. Confirm the exact video. |

## Block private data with Presidio, and guard your own agent

| # | Pick | Author, year | Kind | Bar |
| - | ---- | ------------ | ---- | --- |
| 1 | Presidio documentation (analyzer, anonymizer, custom recognizers) | Microsoft, ongoing | read | Official docs of the tool the step uses. |
| 2 | Presidio, data protection and de-identification (conference or user group talk) | Microsoft Presidio maintainers | video | The team that runs it. Confirm that a talk exists and pick one. |
| 3 | OWASP LLM02 sensitive information disclosure | OWASP GenAI Security Project, 2025 | read | The standards page for the risk this part closes. |
| 4 | Extracting training data from large language models (arXiv 2012.07805) | Carlini et al., 2021 | read | The original paper. Shows private text can come back out. |
| 5 | Scalable extraction of training data from production language models (arXiv 2311.17035) | Nasr et al., 2023 | read | The authors' follow up on production models. |
| 6 | Special category data (health data) | UK Information Commissioner's Office, ongoing | read | The regulator. Why an allergy note needs extra care. |
| 7 | Guide to protecting the confidentiality of personally identifiable information (SP 800-122) | NIST, 2010 | read | A standards body. Evergreen on what counts as PII. |
| 8 | The four question frame for threat modeling | Adam Shostack, ongoing | read | The author of the method. A short frame for the capstone plan. |
| 9 | Threat modeling AI and ML systems and dependencies | Microsoft, ongoing | read | A team that runs the practice. Maps onto the tools table in the plan. |
| 10 | OWASP AI Exchange | OWASP AI Exchange project, ongoing | read | A community standard with a maintained threat list. Keep one page only. |
