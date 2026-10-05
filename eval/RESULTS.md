# Eval results

40 postings labeled by hand. Model: jev-1.13.0. Ids 21-40 were labeled blind; ids 1-20 were revised after seeing Jev's answers (originals in `labels_batch1_before_review.csv`), and `requires_ml_background` was relabeled to its strict definition after review for all rows.
The set is stratified by Jev's bucket (see `make_set.py`), so these numbers describe each bucket, not the accuracy of a random posting.

## Per question

| Question | All | Ids 1-20 (revised) | Ids 21-40 (blind) |
|---|---|---|---|
| role_kind | 31/40 (78%) | 16/20 (80%) | 15/20 (75%) |
| ai_scope | 18/40 (45%) | 8/20 (40%) | 10/20 (50%) |
| seniority | 27/40 (68%) | 13/20 (65%) | 14/20 (70%) |
| requires_ml_background | 36/40 (90%) | 19/20 (95%) | 17/20 (85%) |
| requires_hands_on_ai | 31/40 (78%) | 17/20 (85%) | 14/20 (70%) |
| requires_engineering_background | 34/40 (85%) | 17/20 (85%) | 17/20 (85%) |
| bucket | 26/40 (65%) | 15/20 (75%) | 11/20 (55%) |

ai_scope as the buckets use it (AI vs not AI, native and platform merged): 33/40 (82%).
Bucket, leaving out the 4 rows Jev sent to review: 26/36 (72%).
In an AI bucket or not (the three AI buckets vs the rest), same rows: 32/36 (89%).

Seniority within one level: 40/40 (100%).

## Per Jev bucket (precision: of the rows Jev put here, how many belong)

| Jev bucket | Correct | Human bucket for the misses |
|---|---|---|
| ai_program_or_tpm | 5/8 (62%) | ai_pm_no_ml_required 2, not_a_fit 1 |
| ai_pm_no_ml_required | 5/7 (71%) | ai_pm_ml_required 2 |
| ai_pm_ml_required | 2/4 (50%) | ai_pm_no_ml_required 2 |
| program_or_tpm_non_ai | 4/6 (67%) | ai_program_or_tpm 2 |
| pm_non_ai | 4/5 (80%) | ai_pm_no_ml_required 1 |
| not_a_fit | 6/6 (100%) | - |
| review | 0/4 (0%) | ai_program_or_tpm 3, not_a_fit 1 |

## Disagreements

| id | Title | Question | Jev | Human | Note |
|---|---|---|---|---|---|
| 1 | Field Technical Program/Project Manager | ai_scope | not_ai | unclear |  |
| 1 | Field Technical Program/Project Manager | requires_hands_on_ai | yes | no |  |
| 2 | Research Program Manager – Adversarial Model Resea | seniority | 3 | 4 |  |
| 3 | Product Manager | ai_scope | not_ai | unclear | Previous experience in engineering and/or design roles |
| 3 | Product Manager | seniority | 3 | 2 | Previous experience in engineering and/or design roles |
| 3 | Product Manager | requires_engineering_background | no | yes | Previous experience in engineering and/or design roles |
| 4 | Senior Product Operations Manager | role_kind | program_manager | product_manager |  |
| 4 | Senior Product Operations Manager | ai_scope | ai_native | ai_platform |  |
| 5 | Program Manager, Product Systems and Insights | role_kind | program_manager | technical_program_manager |  |
| 5 | Program Manager, Product Systems and Insights | ai_scope | not_ai | unclear |  |
| 5 | Program Manager, Product Systems and Insights | seniority | 3 | 2 |  |
| 6 | Technical Program Manager, AI Accelerator Software | ai_scope | ai_platform | ai_native |  |
| 8 | Staff Product Designer | ai_scope | ai_native | ai_platform |  |
| 8 | Staff Product Designer | requires_hands_on_ai | no | yes |  |
| 12 | Forward Deployed Product Manager, Enterprise | requires_engineering_background | no | yes |  |
| 13 | Operations Program Manager / Associate, Industrial | role_kind | program_manager | sales_or_success |  |
| 13 | Operations Program Manager / Associate, Industrial | ai_scope | ai_platform | unclear |  |
| 13 | Operations Program Manager / Associate, Industrial | seniority | 2 | 1 |  |
| 14 | Staff Software Engineer, Enterprise Product | ai_scope | ai_platform | ai_native |  |
| 14 | Staff Software Engineer, Enterprise Product | seniority | 4 | 3 |  |
| 14 | Staff Software Engineer, Enterprise Product | requires_hands_on_ai | no | yes |  |
| 15 | Product Experience Specialist (APAC) | role_kind | sales_or_success | engineering |  |
| 15 | Product Experience Specialist (APAC) | ai_scope | ai_native | not_ai |  |
| 15 | Product Experience Specialist (APAC) | seniority | 2 | 1 |  |
| 17 | Senior Product Manager - Application Performance M | ai_scope | ai_native | ai_platform |  |
| 17 | Senior Product Manager - Application Performance M | requires_ml_background | yes | no |  |
| 17 | Senior Product Manager - Application Performance M | requires_engineering_background | no | yes |  |
| 18 | Staff Product Manager, AI | ai_scope | ai_native | ai_platform |  |
| 19 | Account Executive, Product - Tax | seniority | 4 | 3 |  |
| 20 | Program Manager, Scale Onboarding (London, United  | ai_scope | not_ai | ai_native |  |
| 21 | Product Policy Manager, Product Risk | role_kind | program_manager | product_manager |  |
| 21 | Product Policy Manager, Product Risk | seniority | 3 | 2 |  |
| 22 |  Technical Program Manager, AI & Cloud Efficiency  | ai_scope | ai_platform | ai_native |  |
| 22 |  Technical Program Manager, AI & Cloud Efficiency  | seniority | 3 | 2 |  |
| 23 | Director of Product Management, Fintech | ai_scope | not_ai | unclear |  |
| 23 | Director of Product Management, Fintech | requires_hands_on_ai | no | yes |  |
| 24 | Product Manager | ai_scope | not_ai | ai_platform |  |
| 24 | Product Manager | requires_engineering_background | no | yes |  |
| 26 | Partner Program Lead | ai_scope | not_ai | ai_native |  |
| 26 | Partner Program Lead | requires_hands_on_ai | no | yes |  |
| 28 | Senior Agent Product Manager | requires_hands_on_ai | yes | no |  |
| 29 | Global Senior Equity Program Manager | seniority | 4 | 3 |  |
| 30 | Product Operations Manager | role_kind | program_manager | technical_program_manager |  |
| 30 | Product Operations Manager | ai_scope | not_ai | ai_native |  |
| 30 | Product Operations Manager | requires_hands_on_ai | yes | no |  |
| 31 | Senior Program Manager, Data Operations | ai_scope | ai_platform | ai_native |  |
| 32 | Product Management, Research | seniority | 3 | 2 |  |
| 32 | Product Management, Research | requires_ml_background | no | yes |  |
| 33 | Design Program Manager, Research Operations | role_kind | program_manager | technical_program_manager |  |
| 33 | Design Program Manager, Research Operations | ai_scope | ai_native | ai_platform |  |
| 33 | Design Program Manager, Research Operations | seniority | 3 | 2 |  |
| 35 | Product Manager | Vendor Intelligence & Marketplac | ai_scope | ai_native | ai_platform |  |
| 35 | Product Manager | Vendor Intelligence & Marketplac | requires_ml_background | yes | no |  |
| 35 | Product Manager | Vendor Intelligence & Marketplac | requires_engineering_background | no | yes |  |
| 36 | Staff Product Manager - Technical | ai_scope | ai_platform | ai_native |  |
| 36 | Staff Product Manager - Technical | seniority | 4 | 3 |  |
| 36 | Staff Product Manager - Technical | requires_hands_on_ai | no | yes |  |
| 36 | Staff Product Manager - Technical | requires_engineering_background | no | yes |  |
| 37 | Forward Deployed Product Manager, Public Sector | requires_ml_background | no | yes |  |
| 38 | Business Development Manager, Product & Platform | role_kind | program_manager | product_marketing |  |
| 39 | Program Manager, Public Sector (Commercial Legal) | ai_scope | not_ai | ai_platform |  |
| 39 | Program Manager, Public Sector (Commercial Legal) | requires_hands_on_ai | no | yes |  |
| 40 |  Sales Dev AI Program Manager | role_kind | program_manager | technical_program_manager |  |
