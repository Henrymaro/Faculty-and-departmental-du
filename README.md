# DuesPay System

## 📝 Overview
Engineered for minimal connectivity, the DuesPay System operates as a resilient web platform handling payments across departments and academic staff. Where standard portals fail, its blended offline-online structure maintains continuous recording of transactions and issues receipts regardless of signal strength. Data accuracy remains uncompromised through synchronized storage protocols that activate backup routines when networks drop unexpectedly. Built without dependency on persistent internet links, it sustains functionality where traditional systems would stall or break down completely.

## 🧠 Core Logic & Architecture
When connectivity shifts, operation continues through adaptive pathways shaped by current conditions. State awareness guides each routing decision as execution adjusts without delay.
* With verification of academic status, identification relies on matching an exact matriculation code - such as CMP220 - to entries within a stored institutional dataset. Each check occurs prior to access being granted. Format compliance is required without exception. The system references only registered profiles during validation.
* Should Paystack fail during online attempts, routing shifts automatically. Offline mode activates when connection drops occur. Transactions store safely within local memory under such conditions. A simulated approval appears immediately afterward each time. This avoids halting operations at critical moments. Processing resumes silently once connectivity returns eventually.
* When connection drops, a local SQLite database stores transaction details - such as whether charges belong to departments or faculty units - ensuring no data loss. Restoration of internet triggers automatic alignment with central ledgers. Information remains consistent across systems despite interruptions. Updates occur silently without user intervention. Structure supports reliable audit trails even during outages.

## 🤖 AI Prompting Strategy & QA Journey
*Code behind this effort came into being through coordinated use of large language systems. A look at how prompts were shaped follows, revealing steps taken to move from idea toward error-free output.*

### 1. System Architecture (The Master Prompt)
Before introducing logic, clarity about environmental limits was necessary. Core infrastructure demands were outlined early, with priority given to functioning without connectivity. This foundation shaped how the system later responded to inputs.

> Act as a senior systems architect. We are building the 'DuesPay System', a web-based portal for students to pay 'Departmental Due' or 'Faculty Due'. The primary constraint is that it MUST work in a low-connectivity environment without an internet connection. Build the backend using Python, Flask, and SQLite. Include a student login mechanism using a 'Matric No' identifier (format: CMP220****) and pre-populate 10 student accounts. Provide the overarching data models and the routing structure before writing any frontend code.

### 2. Logic Verification & Debugging (The QA Prompt)
At first evaluation, whenever connectivity failed, the system stopped entirely - this broke the essential offline function. A typical Paystack setup had been applied, yet it could not handle disconnections. To prevent total failure, changes were introduced beneath the structure. The fix ensured operations continued despite missing network signals. Without intervention, the logic would have ignored fundamental constraints.

> The Paystack integration you provided crashes the app with a timeout error when the internet fails. This violates the core offline capability requirement. Rewrite the payment processing function using a strict try-except block. If the Paystack API request fails due to a network error, the except block must simulate a successful transaction locally, log the payment status in the SQLite database, and still generate the receipt for the student so their workflow isn't interrupted.

### 3. Edge-Case Refinement
Once the payment cycle reached equilibrium, precision in structural rules became necessary. Compliance with official documentation standards followed naturally. Receipt outputs then aligned correctly within the organizational framework. Avoidance of vague default entries emerged as a consequence. System behavior adjusted without further intervention.

> Update the receipt generation logic to enforce specific pricing parameters depending on whether 'Departmental Due' or 'Faculty Due' was selected. Additionally, remove any placeholder university names you generated. The receipt header must explicitly read 'UNIVERSITY OF DELTA, AGBOR' and the sub-header must be 'DEPARTMENT OF SOFTWARE ENGINEERING'.

## ⚙️ Technologies Used
* **System Orchestration:** Managing System Workflows Through Prompt Design and Language Model Context Control
* **Validation:** Logic Checks and Testing
* **Core Stack:** Python forms the foundation. Following that, Flask supports web handling tasks. Afterward, SQLite manages data storage needs.
* **Integrations:** Paystack API Architecture
