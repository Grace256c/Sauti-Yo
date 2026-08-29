# Sauti Yo

### Know. Act. Be Heard.

**A phone-first Rights-to-Action platform for legal and policy access in Uganda.**

Sauti Yo helps people recognise when an everyday problem may involve their rights, understand verified legal information in plain language, identify practical next steps, connect to trusted support, and safely make their voices heard.

> **Access to useful rights information should not depend on owning a smartphone, having mobile data, or knowing legal terminology.**

Sauti Yo combines **USSD, SMS, Voice/IVR, Web and Chat** around one shared Rights-to-Action engine so people can access guidance through the communication channel available to them.

Built for the **Africa's Talking Women in Tech Hackathon 2026 — Legal & Policy Advocacy Track, Kampala, Uganda.**

---

## The Problem

Legal rights may exist on paper while remaining difficult to use in everyday life.

Someone experiencing domestic violence, child abuse, unfair treatment, an employment problem, a land dispute, or another rights issue may face several barriers before ever reaching a lawyer or institution:

- They may not recognise that what is happening involves a legal right.
- Reliable information may be difficult to find.
- Legal language may be difficult to understand.
- Knowing the law does not automatically explain what to do next.
- People may not know which trusted organisation can help.
- Smartphone ownership, mobile data and reliable internet access cannot be assumed.
- Language and literacy can make digital legal information inaccessible.
- Community experiences rarely become structured, privacy-conscious information that organisations can learn from.

Sauti Yo addresses the gap between **having rights** and being able to **understand and act on those rights**.

---

## Our Solution

Sauti Yo transforms verified legal and policy information into a structured **Rights-to-Action** journey.

```text
RECOGNISE
    ↓
UNDERSTAND
    ↓
ACT
    ↓
CONNECT
    ↓
BE HEARD
```

### Recognise

Users describe what is happening in ordinary language without needing to know legal terminology.

### Understand

Sauti Yo connects the situation to relevant verified rights information and explains it in accessible language.

### Act

The platform provides practical next steps rather than stopping at legal information.

### Connect

Users can identify appropriate verified support organisations and services and, where suitable, move into referral pathways.

### Be Heard

Users may voluntarily contribute privacy-conscious feedback through **Community Voice**, helping organisations understand barriers communities experience when seeking help.

---

# Core Platform

## 1. Rights-to-Action Engine

The Rights-to-Action engine is the core of Sauti Yo.

Instead of behaving like a legal dictionary, the platform starts with the person's situation and connects:

```text
Situation
   ↓
Rights information
   ↓
Practical actions
   ↓
Safety guidance
   ↓
Support services
   ↓
Optional referral
```

The same backend services support Web, USSD, SMS, Voice and Chat so citizens can receive consistent guidance across channels.

This **one engine, many channels** architecture is central to Sauti Yo.

---

## 2. Web Experience

The web application provides a visual pathway into Sauti Yo for people with smartphone or computer access.

The citizen-facing experience supports:

- Rights categories
- Situation-based exploration
- Rights-to-Action results
- Practical next steps
- Support information
- Legal chat
- Responsive mobile and desktop layouts

The web experience complements rather than replaces the phone-first channels.

---

## 3. USSD

Sauti Yo provides feature-phone access through Africa's Talking USSD.

The USSD experience supports:

- Language selection
- Situation-first navigation
- Rights categories and issues
- Rights-to-Action guidance
- Practical next steps
- Support information
- High-risk safety pathways
- Emergency-support information
- Safe exit flows
- Short session-friendly menus

USSD is particularly important because it does not require a smartphone or mobile-data connection.

### Sandbox Verification

The Sauti Yo USSD integration has been tested end-to-end using the Africa's Talking Sandbox.

Current Sandbox service code:

```text
*384*163024#
```

The verified development flow is:

```text
Africa's Talking Simulator
        ↓
USSD service code
        ↓
Africa's Talking
        ↓
Public HTTPS callback
        ↓
Django USSD handler
        ↓
Rights-to-Action engine
        ↓
USSD response
```

---

## 4. SMS

SMS allows users to describe situations, request rights information, receive practical guidance and continue selected support flows using an ordinary text-message interface.

The SMS workflow supports:

- Situation matching
- Rights information
- Practical action guidance
- Support contacts
- High-risk safety check-ins
- Follow-up conversations
- Normal and discreet message formats
- Language commands
- Referral workflows
- Rate limiting
- Controlled AI-assisted rewording
- Safe fallback behaviour

### Two-Way Shortcode Integration

Sauti Yo uses Africa's Talking's two-way SMS functionality for shortcode conversations.

Current Sandbox shortcode:

```text
18275
```

When Africa's Talking forwards an incoming shortcode message, Sauti Yo receives information including:

```text
from
to
text
linkId
```

Sauti Yo preserves the incoming `linkId` and uses Africa's Talking premium/on-demand SMS functionality when replying.

This allows the citizen's interaction to remain associated with the same shortcode conversation:

```text
18275

Citizen:
WORK

18275:
Sauti Yo: Understand your workplace issue, learn about
relevant rights and find practical next steps...
```

The verified Sandbox flow is:

```text
Citizen / Simulator
        ↓
18275
        ↓
Africa's Talking
        ↓
POST /api/channels/sms/
        ↓
Sauti Yo SMS handler
        ↓
Rights-to-Action engine
        ↓
send_premium(..., link_id=...)
        ↓
Africa's Talking
        ↓
18275 conversation
```

The two-way shortcode flow has been verified end-to-end in the Africa's Talking Sandbox.

Sensitive information is not treated as ordinary bulk messaging. High-risk situations use controlled safety flows, and citizens retain control over follow-up interactions.

---

## 5. Voice / IVR

Voice support is being developed as an accessibility channel for people who may find text-heavy interfaces difficult to use.

The Voice/IVR architecture includes:

- Telephone-based interaction
- Spoken language selection
- Keypad navigation
- Situation navigation
- Rights-to-Action prompts
- Support information
- Emergency-support pathways
- Africa's Talking Voice callbacks
- Voice-session state management
- Infrastructure for recording/transcription where appropriate

Africa's Talking Voice connectivity and spoken menu delivery have been integrated and tested.

**Current validation status:** keypad-driven multi-step IVR navigation remains under active integration testing and should not yet be treated as production-ready.

Voice is therefore an active MVP integration rather than a fully validated production channel.

---

## 6. Ask Sauti Yo — Legal Chat

Sauti Yo includes a conversational legal-information interface.

Users can ask direct legal questions such as:

```text
What does Article 24 of the Constitution say?
```

or describe situations in ordinary language:

```text
My husband is beating me. What can I do?
```

The chatbot combines:

- Situation recognition
- Rights-to-Action content
- Verified legal retrieval
- Conversation context
- Explicit constitutional Article/Section retrieval
- Practical action guidance
- Safety information
- Support information
- Controlled fallback behaviour when external AI services are unavailable

Conversation context allows follow-up questions to remain connected to a user's active situation without incorrectly forcing unrelated questions into an earlier topic.

---

# Verified Legal Knowledge

Sauti Yo separates **verified legal sources** from generated explanations.

The legal knowledge layer currently includes the:

**Constitution of the Republic of Uganda**

Legal provisions can be stored as structured records containing information such as:

- Document
- Provision type
- Article or section number
- Heading
- Full text
- Source information
- Jurisdiction
- Version or effective information
- Active status

Explicit legal references are resolved carefully.

For example:

```text
Article 24
```

is treated differently from:

```text
Section 24
```

The retrieval system also avoids guessing when the same section number could refer to provisions in multiple legal documents.

This matters because a legal-information system should prefer saying that it cannot safely identify a provision over confidently returning the wrong law.

---

# Safety by Design

Legal access can involve highly sensitive situations.

Sauti Yo therefore treats safety as part of the architecture rather than an optional feature.

### Data Minimisation

Collect only information necessary for the interaction.

### User-Controlled Communication

Citizens should retain control over sensitive follow-up communication.

### Discreet Communication

Where appropriate, SMS flows can use less revealing wording.

### High-Risk Pathways

Sensitive situations can use predefined and reviewed guidance instead of unrestricted generated responses.

### Safety Check-Ins

High-risk SMS situations can trigger controlled prompts checking whether the citizen is currently safe before continuing the normal information flow.

### Verified Referrals

Support organisations and contact information should be verified before being presented as trusted support.

### No Automatic Intervention

Sauti Yo does not automatically contact police, relatives, organisations or other third parties on behalf of a citizen.

### Clear Limitations

Sauti Yo provides general legal and rights information. It is not a replacement for a lawyer, emergency service or authorised institution.

---

# Responsible AI

Sauti Yo uses AI as an **enabling layer**, not as the legal authority.

The intended architecture is:

```text
User question
      ↓
Situation classification
      ↓
Verified content retrieval
      ↓
Rights-to-Action context
      ↓
Safety controls
      ↓
Plain-language response
```

AI may assist with:

- Situation classification
- Retrieval
- Plain-language explanation
- Conversational interaction
- Rewording appropriate content

AI must **not**:

- Invent Ugandan law
- Invent legal provisions
- Invent support organisations or contacts
- Present itself as a lawyer
- Make emergency decisions for the user
- Override approved high-risk safety flows
- Turn unverified content into verified legal information

When sufficient verified information cannot be found, Sauti Yo should say so rather than fabricate an answer.

For sensitive or high-risk situations, predefined and reviewed guidance takes priority over unrestricted AI generation.

---

# Multilingual Access

Sauti Yo is designed for multilingual access.

The phone-channel architecture supports:

- **English**
- **Luganda**
- **Kiswahili**
- **Runyankole / Nyankore**

The web experience currently prioritises English while multilingual content is expanded and reviewed.

Legally sensitive translations should be human-reviewed before being treated as verified citizen-facing legal content.

Language is an accessibility layer; the core innovation remains the Rights-to-Action journey.

---

# Support & Referral Workflows

Sauti Yo includes backend support for trusted organisations, support services and citizen referrals.

The support/referral layer enables the system to:

- Maintain support organisations
- Store service contact information
- Identify emergency services
- Connect situations to relevant services
- Create citizen referrals
- Track referral status
- Maintain referral history
- Support partner-facing workflows
- Protect partner information through API permissions

This moves Sauti Yo beyond information delivery toward an **information-to-action** model.

---

# Community Voice

Sauti Yo is designed not only to deliver information to communities but also to provide a privacy-conscious way for communities to be heard.

After receiving guidance, users may voluntarily answer short questions such as:

> What makes it hardest for people in your community to get help?

Possible responses might include:

- Not knowing where to go
- Cost
- Distance
- Fear of retaliation
- Stigma
- Other barriers

The goal is not to build individual behavioural profiles.

Community Voice information should be used in aggregate so partner organisations can better understand barriers and improve programmes, outreach and policy engagement.

---

# System Architecture

```text
                         ┌───────────────────────┐
                         │       CITIZENS        │
                         └───────────┬───────────┘
                                     │
           ┌─────────────┬───────────┼───────────┬─────────────┐
           │             │           │           │             │
           ▼             ▼           ▼           ▼             ▼
         USSD           SMS       Voice/IVR      Web           Chat
           │             │           │           │             │
           └─────────────┴───────────┴───────────┴─────────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    Django REST API    │
                         └───────────┬───────────┘
                                     │
          ┌──────────────────────────┼─────────────────────────┐
          │                          │                         │
          ▼                          ▼                         ▼
 ┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
 │ Rights-to-Action│      │ Legal Knowledge  │      │ Safety &        │
 │ Engine          │      │ Retrieval        │      │ Channel Logic   │
 └────────┬────────┘      └─────────┬────────┘      └────────┬────────┘
          │                         │                        │
          └─────────────────────────┼────────────────────────┘
                                    │
                                    ▼
                         ┌───────────────────────┐
                         │      PostgreSQL       │
                         │                       │
                         │ Rights                │
                         │ Legal knowledge       │
                         │ Support services      │
                         │ Referrals             │
                         │ Partner data          │
                         │ Feedback              │
                         └───────────────────────┘

                     Africa's Talking
                     ├── USSD
                     ├── SMS
                     └── Voice
```

All citizen channels are designed to use the same underlying Rights-to-Action services rather than operating as disconnected applications.

---

# Technology Stack

## Backend

- Python
- Django
- Django REST Framework
- PostgreSQL
- Django caching
- OpenAI integration for supported AI functionality
- `pypdf` for legal-document ingestion

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Lucide icons

## Telecommunications

- Africa's Talking APIs and Python SDK
- USSD
- Two-way / premium SMS
- Voice / IVR

## Infrastructure & Development

- Docker
- Docker Compose
- Git
- GitHub
- Gunicorn / Nginx-compatible deployment architecture
- HTTPS tunnelling for development callbacks

---

# Project Structure

```text
Sauti-Yo/
│
├── backend/
│   ├── apps/
│   │   ├── channels/
│   │   │   ├── sms/
│   │   │   ├── ussd/
│   │   │   └── voice/
│   │   │
│   │   ├── chat/
│   │   ├── legal_knowledge/
│   │   ├── rights/
│   │   ├── content/
│   │   ├── support/
│   │   ├── partners/
│   │   ├── referrals/
│   │   └── core/
│   │
│   ├── config/
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   └── ...
│   ├── package.json
│   └── vite.config.*
│
├── legal_sources/
│   └── uganda_constitution_2023.pdf
│
├── docker-compose.yml
└── README.md
```

---

# Important API Routes

The backend exposes APIs under `/api/`.

Key routes include:

```text
/api/rights/
/api/rights/analyse/
/api/support/

/api/channels/ussd/
/api/channels/sms/
/api/channels/voice/

/api/chat/
/api/partners/
/api/referrals/
```

These APIs allow the frontend and Africa's Talking communication channels to use shared backend services.

---

# Local Development

## Prerequisites

Install:

- Python 3
- Node.js and npm
- PostgreSQL
- Git

Additional services may be required depending on the development configuration being used.

---

## 1. Clone the Repository

```bash
git clone https://github.com/Grace256c/Sauti-Yo.git
cd Sauti-Yo
```

---

## 2. Create a Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file using the project's `.env.example` as a guide where available.

Typical development configuration includes:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

FRONTEND_URL=http://localhost:5173

POSTGRES_DB=sautiyo
POSTGRES_USER=sautiyo
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

OPENAI_API_KEY=your_openai_key

AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your_africastalking_key
AFRICASTALKING_SMS_SENDER_ID=
```

For a public development callback, add the public hostname to `ALLOWED_HOSTS`.

Example:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,your-public-host.example
```

When `DEBUG=True`, `*.ngrok-free.dev`, `*.ngrok-free.app`, `*.ngrok.app`, `*.ngrok.io` and `*.trycloudflare.com` hostnames are allowed automatically, so ngrok/Cloudflare tunnels work without editing `ALLOWED_HOSTS` on every restart. Manually adding a hostname is only needed for other tunnel providers or custom domains.

**Never commit real API keys, credentials or passwords.**

---

## 5. Prepare PostgreSQL

Ensure PostgreSQL is running and that the configured database exists.

---

## 6. Apply Django Migrations

```bash
cd backend
python manage.py migrate
```

---

## 7. Import Verified Legal Material

Where the legal source file is available, the legal knowledge system can import the Constitution using the project's management command.

From `backend/`:

```bash
python manage.py import_constitution \
  --pdf ../legal_sources/uganda_constitution_2023.pdf
```

This converts constitutional provisions into structured legal records for retrieval.

---

## 8. Seed Project Content

Where required, load the project's pilot content:

```bash
python manage.py seed_pilot_content
```

---

## 9. Run the Backend

From `backend/`:

```bash
python manage.py runserver 8000
```

The development API will normally be available at:

```text
http://127.0.0.1:8000/api/
```

A `404` at the bare Django root during development does not necessarily indicate that the API is unavailable.

---

## 10. Run the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173/
```

During local development, Vite can proxy `/api/` requests to Django.

---

# Africa's Talking Integration

Sauti Yo uses Africa's Talking to extend Rights-to-Action beyond the web.

The Django backend exposes:

```text
USSD  → /api/channels/ussd/
SMS   → /api/channels/sms/
Voice → /api/channels/voice/
```

For external callbacks, Django must be reachable through a public HTTPS URL.

During development this can be achieved using an appropriate secure tunnel.

Example callback configuration:

```text
https://your-public-host.example/api/channels/ussd/
https://your-public-host.example/api/channels/sms/
https://your-public-host.example/api/channels/voice/
```

Do not commit temporary tunnel domains or API credentials into application source code.

## USSD Sandbox

Current tested Sandbox service code:

```text
*384*163024#
```

USSD has been verified through the Africa's Talking simulator.

## SMS Sandbox

Current tested Sandbox shortcode:

```text
18275
```

Incoming SMS callbacks include the originating phone number, shortcode, message text and Africa's Talking `linkId`.

For two-way shortcode replies, Sauti Yo carries the incoming `linkId` through the SMS request and uses the premium SMS API.

This keeps responses associated with the shortcode interaction instead of treating them as unrelated bulk SMS.

## Voice Integration

Voice callbacks use:

```text
/api/channels/voice/
```

Voice connectivity and spoken menu delivery have been integrated.

Multi-step keypad navigation remains under active validation.

---

# Testing

The backend contains automated tests covering the major application areas.

Run the complete backend suite:

```bash
cd backend
python manage.py test
```

Run chatbot tests:

```bash
python manage.py test apps.chat
```

Run legal-knowledge tests:

```bash
python manage.py test apps.legal_knowledge
```

Run channel-specific tests:

```bash
python manage.py test apps.channels.sms
python manage.py test apps.channels.ussd
python manage.py test apps.channels.voice
```

Check Django configuration:

```bash
python manage.py check
```

The two-way SMS changes have been regression-tested against the SMS test suite.

Before release or final integration, run the complete backend suite again rather than relying on a previously recorded test count.

---

# Frontend Verification

Create a production frontend build with:

```bash
cd frontend
npm run build
```

This should be run after significant frontend integration changes and before deployment.

---

# Demonstration Flows

## USSD

Using the Africa's Talking Sandbox simulator:

```text
Dial *384*163024#
        ↓
Select language
        ↓
Choose Find my rights / Get help now
        ↓
Select a situation
        ↓
Receive Rights-to-Action guidance
        ↓
View actions or support
```

## SMS

Using the Sandbox simulator:

```text
Open SMS
        ↓
Send a situation to 18275
        ↓
Sauti Yo classifies the situation
        ↓
Receive response in the 18275 conversation
        ↓
Continue safety / rights / support flow
```

Example:

```text
Citizen → WORK

Sauti Yo → Understand your workplace issue, learn about
relevant rights and find practical next steps...
```

For a high-risk situation, the system can first enter a controlled safety flow before continuing with normal Rights-to-Action guidance.

## Web

```text
Open Sauti Yo
        ↓
Describe or select a situation
        ↓
Explore relevant rights
        ↓
Review practical actions
        ↓
Find trusted support
```

---

# Current MVP Capabilities

The integrated MVP includes:

- Rights-to-Action backend
- Citizen web experience
- Rights categories
- Situation analysis
- USSD integration
- Two-way SMS integration
- Voice / IVR integration under active validation
- Multilingual phone-channel architecture
- Legal chatbot
- Conversation-aware chatbot follow-ups
- Verified constitutional retrieval
- Explicit Article/Section resolution
- Safe legal-retrieval fallback
- Support-service directory
- Partner workflows
- Citizen referral creation
- Referral status/history tracking
- Community-oriented feedback architecture
- Africa's Talking callbacks
- Automated backend regression tests

---

# Current Legal Knowledge Scope

The verified legal knowledge database currently focuses on the:

> **Constitution of the Republic of Uganda**

The architecture is designed so additional verified Ugandan legal documents can be introduced later.

Potential expansion areas include:

- Domestic and family safety
- Employment
- Land and inheritance
- Child protection
- Digital rights
- Education and public policy
- Consumer and mobile-money rights

Additional legal sources should be verified and reviewed before becoming trusted citizen-facing content.

---

# Privacy Principles

Sauti Yo follows a privacy-conscious model.

The platform should not treat personal stories as a commercial dataset.

Key principles include:

- Data minimisation
- Purpose limitation
- User-controlled communication
- Anonymous or aggregated Community Voice reporting
- Role-based partner access
- No unnecessary collection of sensitive incident details
- No sale of individual legal questions or personal stories

The long-term principle is:

> **We monetise the service — not the person.**

---

# Business & Sustainability Model

Sauti Yo is designed as a public-interest platform with a **B2B2C / partnership-supported model**.

Citizens are the primary beneficiaries, while sustainability can come through partnerships with organisations such as:

- Legal-aid organisations
- Civil-society organisations
- NGOs
- Development partners
- Public-interest programmes
- Policy organisations
- Research and advocacy programmes

Potential institutional services include:

- Verified rights-awareness campaigns
- Community consultation
- Aggregate insight
- Programme deployments
- Institutional Rights-to-Action integrations
- Sponsored public-interest access

Essential rights information should remain accessible without requiring vulnerable citizens to purchase a Sauti Yo subscription.

---

# Roadmap

Beyond the hackathon MVP, Sauti Yo can expand through:

### Legal Coverage

Add reviewed legal sources covering employment, land and inheritance, child protection, digital rights and other areas.

### Language Coverage

Expand professionally reviewed Luganda, Kiswahili, Runyankole and other Ugandan-language content.

### Voice Accessibility

Complete keypad-flow validation and expand reviewed local-language Voice/IVR prompts and spoken journeys.

### Legal Knowledge Retrieval

Grow the verified legal knowledge base and strengthen verified-source retrieval.

### Partner Ecosystem

Expand the verified support directory and partner/referral network.

### Community Insight

Strengthen privacy-conscious Community Voice and policy-feedback workflows.

### Campaigns

Enable trusted organisations to distribute verified rights and public-interest information through Sauti Yo's phone channels.

---

# Design Principles

Sauti Yo development follows these principles:

1. **Phone first** — the core journey should remain useful without a smartphone.
2. **Situation first** — users should not need legal terminology.
3. **Action over information** — explain what someone can practically do next.
4. **Verified before generated** — authoritative content comes before AI.
5. **Safety before sophistication** — high-risk pathways must remain controlled.
6. **One engine, many channels** — USSD, SMS, Voice, Web and Chat share core logic.
7. **Privacy by design** — collect and expose as little sensitive information as necessary.
8. **Human review for legal content** — especially translations and high-risk guidance.
9. **Accessibility is core** — connectivity, device type, language and literacy influence design.
10. **Do not guess** — when verified information is insufficient, say so.

---

# Why Sauti Yo Is Different

Sauti Yo is not simply:

- A legal chatbot
- A legal-document repository
- A smartphone application
- A USSD menu
- An SMS bot
- An AI demonstration

Its value comes from connecting those technologies around one journey:

```text
A person describes what is happening
                ↓
Sauti Yo helps recognise the issue
                ↓
Verified rights information is retrieved
                ↓
The information is made understandable
                ↓
Practical next steps are provided
                ↓
Trusted support can be identified
                ↓
The person chooses what happens next
                ↓
Optional anonymous experience contributes
to wider community insight
```

That is the **Rights-to-Action** model.

---

# Hackathon

**Africa's Talking Women in Tech Hackathon 2026**

**Track:** Legal & Policy Advocacy

**Location:** Kampala, Uganda

### One-Sentence Pitch

> **Sauti Yo turns verified rights information into practical action through USSD, SMS and Voice — no smartphone or mobile data required.**

### Product Message

> **Know. Act. Be Heard.**

**Verified rights information. Practical next steps. Trusted support. Accessible on the phone people already have.**

---

# Disclaimer

Sauti Yo provides general legal and rights information intended to improve access to understandable guidance and support.

It does **not** provide legal representation and should not be treated as a substitute for advice from a qualified lawyer, authorised institution, emergency service or other appropriate professional.

Legal content, translations, support information and high-risk guidance should be reviewed before production use.

---

# Contributing

Sauti Yo is under active development.

When contributing:

1. Keep changes focused.
2. Do not commit credentials or secrets.
3. Add or update tests when backend behaviour changes.
4. Run the relevant test suites before submitting changes.
5. Run `python manage.py check`.
6. Verify frontend builds when frontend code changes.
7. Preserve the verified-content and safety architecture.
8. Do not introduce unverified legal claims into citizen-facing content.

---

# Project Status

**Hackathon MVP — Active Development**

### Verified During Current Integration

- Citizen web application integrated
- Rights-to-Action backend integrated
- Africa's Talking USSD Sandbox working end-to-end
- Africa's Talking two-way SMS Sandbox working end-to-end
- SMS responses returning inside the `18275` shortcode conversation
- High-risk SMS safety flow functioning
- Legal chatbot and legal-knowledge architecture integrated
- Support and referral architecture integrated
- Partner workflows integrated

### Under Active Validation

- Voice/IVR multi-step keypad navigation
- Final cross-channel integration
- Final frontend polish
- Full regression verification before release

---

<div align="center">

## SAUTI YO

### Know. Act. Be Heard.

**Rights information should lead to action — on any phone.**

</div>