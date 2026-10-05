# Investigation Notes

## 1. Public entry point
The assignment specifies the CoA Online Directory of Architects. The live page currently links six search categories:
- Search By Name
- Year of Registration
- Registration Number
- State
- City
- Pincode

Each category is routed through `search_arch2.php` with `searCat=1..6`.

## 2. Access observations
As observed on 05-10-2026, the directory page states that an IP can make three searches per day without subscription and that unlimited access requires subscription. Category search pages display a case-sensitive security-code challenge.

## 3. Security design
The pipeline does not defeat the security code. `app/parser.py::detect_captcha()` identifies security-verification language. `app/extractor.py` stores an event, changes the job status to `captcha_required`, and returns control to the operator.

## 4. Response parsing
The parser uses BeautifulSoup and dynamically reads table headers, allowing fields to be mapped without assuming a single fixed column order. It captures name, registration number, city and validity where displayed and leaves the remaining schema fields nullable for richer record responses.

## 5. Public paginated evidence
The CoA public site also exposes paginated HTML lists. The accessible public list showed 1,161 pages in one related public list and records with registration number, city and validity. This demonstrates that the source uses server-rendered HTML tables and pagination in at least some public flows.

## 6. Chosen architecture
Requests session -> rate limiter/retry -> response capture -> CAPTCHA detector -> HTML parser -> normalization/validation -> SQLite transaction -> dashboard/API/export.

The database commits records immediately, so an interruption does not require the entire run to restart.
