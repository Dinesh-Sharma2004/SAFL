# Rationale Note: AI-related Policy Activity Across Indian States

I focused on **state-government action involving AI**, not every news story that mentions artificial intelligence. Relevant activity includes state AI policies and missions, task forces and centres of excellence, AI in public services, government partnerships, AI-specific funding, regulation and AI infrastructure.

## Sources and state coverage

I used Google News RSS for the main discovery because it supports similar searches across states and brings together reports from different publishers. I grouped searches into four themes: policy and institutions; government deployments; partnerships and funding; and regulation and infrastructure. I also configured direct regional RSS feeds from *The Hindu* and *The Indian Express* for Andhra Pradesh, Telangana, Karnataka, Tamil Nadu, Kerala, Maharashtra, Uttar Pradesh and Rajasthan. These states have extra feeds because suitable regional feeds were available, not because I assumed they had more AI activity.

The search covers all 28 states. I did not rank states by article count: RSS availability and publisher coverage vary, so a low count does not mean a state has no AI activity.

## Collection and processing

The notebook fetches RSS entries and extracts each headline, short summary, publisher, article URL and publication date. I clean HTML and extra spaces, standardise state names, parse dates consistently, leave missing dates blank and remove common tracking parameters from URLs.

I remove exact duplicates using state and normalised URL. I then compare headlines within each state to catch the same announcement reported by different outlets. A similarity score of 91 or above indicates a likely duplicate when dates are within four days. If dates are missing, headline similarity is used. Where possible, I keep a direct publisher link as the main record and retain details of other reports.

## Screening and presentation

A story becomes an **include candidate** only when its headline or RSS summary shows an AI connection, a concrete action and a government or public-sector actor linked to that action. I group candidates into seven types: policy and strategy; institutions; government deployment; partnerships; funding; regulation and ethics; and infrastructure. Unclear matches go to a review queue. Private product launches and general digitisation stories without a clear AI-policy link are not treated as candidates.

The dashboard presents activity by state, type and policy stage, with dates, source links and screening evidence. This makes the records easier to explore and check against original reports. Review status stays visible because an RSS match is a lead to verify, not proof that a policy was implemented. The dataset is a news-based sample, not a complete official inventory.

## Use of AI tools

I used AI to help with documentation, dashboard construction, and drafting or refining some search keywords and feed URL entries. The project decisions—scope, sources, inclusion rules and presentation—were mine. I performed and checked the extraction, cleaning, normalisation, deduplication and other dataset preprocessing myself. AI did not make the final relevance decisions or create facts about the announcements; candidates still require my manual verification.
