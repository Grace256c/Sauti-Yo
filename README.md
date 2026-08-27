# Sauti Yo

**Know. Act. Be Heard.**

Sauti Yo is a Rights-to-Action platform designed to make verified legal information and practical support easier to access in Uganda through the **Web, SMS, USSD, and Voice**.

The platform helps users describe what is happening, understand relevant rights, receive practical next steps, and connect with appropriate support services.

---

## 🌍 Why Sauti Yo?

Access to legal information can be difficult for people who:

- Do not know which rights apply to their situation
- Cannot easily access legal professionals
- Have limited or unreliable internet access
- Use basic or feature phones
- Need information in a familiar language
- Need practical next steps rather than complicated legal terminology

Sauti Yo is designed around a simple idea:

> **Legal information should be understandable, accessible, practical, and available through the technology people already use.**

---

## ✨ Core Features

### 🌐 Web Rights-to-Action

The web platform provides:

- Citizen situation navigation
- Rights and legal information
- Practical action steps
- Safety-aware guidance
- Support and referral information
- Access to the Sauti Yo Legal Information Assistant

The web interface is intentionally **English-only for the current MVP**.

---

### 💬 Legal Information Assistant

Sauti Yo includes a web-based conversational legal information assistant.

The assistant:

- Accepts natural-language questions
- Matches user situations to existing Rights-to-Action guidance
- Uses Sauti Yo's legal knowledge base
- Searches imported sections of the Constitution of Uganda
- Provides practical next steps where verified information exists
- Identifies relevant support services
- Uses safe fallback responses when AI is unavailable
- Avoids presenting unverified legal information as fact

For example, a user may describe a situation such as:

> "My husband keeps beating me every day."

The system can identify this as a domestic-violence situation and connect the user to the relevant Rights-to-Action information and support pathway.

---

## 📱 SMS

Sauti Yo supports rights information through SMS for people using basic mobile phones.

The SMS channel includes:

- Situation matching
- Rights information
- Practical next steps
- Follow-up flows
- Safety checks for high-risk situations
- Support contacts
- Multilingual responses

### Supported SMS languages

- English
- Luganda
- Kiswahili
- Runyankole

---

## 📟 USSD

Sauti Yo provides USSD access so that users do not need a smartphone or mobile application to access basic rights information.

The USSD channel includes:

- Language selection
- Situation navigation
- Rights information
- Action-step menus
- Safety-aware flows
- Support information

### Supported USSD languages

- English
- Luganda
- Kiswahili
- Runyankole

---

## ☎️ Voice

Sauti Yo also contains a Voice/IVR channel.

The Voice integration includes:

- Voice webhook handling
- IVR flows
- Voice session management
- Recording handling
- Voice transcription
- Situation processing
- Direct connection to support numbers where configured

Production Voice functionality requires the appropriate provider configuration and credentials.

---

## ⚖️ Rights-to-Action Engine

At the centre of Sauti Yo is the Rights-to-Action system.

Instead of only presenting legal text, the system connects a user's situation to practical information.

The platform structures information around concepts such as:

```text
Situation
    ↓
Rights Topic
    ↓
Legal Information
    ↓
Action Steps
    ↓
Safety Guidance
    ↓
Support Services
```

This allows the same verified information to support multiple channels.

```text
                  Rights-to-Action
                        │
          ┌─────────────┼─────────────┐
          │             │             │
         Web           SMS           USSD
          │             │             │
          └─────────────┼─────────────┘
                        │
                      Voice
```

---

## 📚 Legal Knowledge Base

Sauti Yo contains a legal knowledge component for storing and retrieving verified legal material.

The current implementation includes support for:

- Legal Documents
- Legal Sections
- Constitutional provisions
- Rights Topics
- Situations
- Action Steps
- Safety Responses
- Support Services

The **Constitution of Uganda** can be imported into the application's legal knowledge database and searched by the chatbot.

---

## 🇺🇬 Constitution of Uganda Integration

The project includes a management command for importing the Constitution from a local PDF.

Example:

```bash
python manage.py import_constitution \
  --pdf ../legal_sources/uganda_constitution_2023.pdf
```

The importer extracts constitutional sections and stores them in the legal knowledge database.

The chatbot can then retrieve relevant constitutional material when answering appropriate legal-information questions.

---

## 🌐 Current MVP Languages

| Channel | English | Luganda | Kiswahili | Runyankole |
|---|---|---|---|---|
| Web Interface | ✅ | Later | Later | Later |
| SMS | ✅ | ✅ | ✅ | ✅ |
| USSD | ✅ | ✅ | ✅ | ✅ |
| Voice | ✅* | Provider/content dependent | Provider/content dependent | Provider/content dependent |

\* Voice availability depends on provider and deployment configuration.

---

# 🛠 Technology Stack

## Backend

- Python
- Django
- Django REST Framework
- PostgreSQL
- OpenAI integration for supported AI and voice features
- `pypdf` for Constitution PDF import

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

## Phone Channels

The application contains integrations for:

- SMS
- USSD
- Voice / IVR

The phone-channel architecture is designed for integration with services such as **Africa's Talking**.

---

# 📁 Project Structure

```text
Sauti-Yo/
│
├── backend/
│   ├── apps/
│   │   ├── analytics/
│   │   ├── campaigns/
│   │   ├── channels/
│   │   │   ├── sms/
│   │   │   ├── ussd/
│   │   │   └── voice/
│   │   │
│   │   ├── chat/
│   │   ├── content/
│   │   ├── legal_knowledge/
│   │   ├── partners/
│   │   ├── referrals/
│   │   ├── rights/
│   │   └── support/
│   │
│   ├── config/
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── legal_sources/
│   └── uganda_constitution_2023.pdf
│
├── .env.example
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

# 🚀 Local Development

## 1. Clone the repository

```bash
git clone https://github.com/Grace256c/Sauti-Yo.git
cd Sauti-Yo
```

---

## 2. Create a Python virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

## 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

---

## 4. Configure environment variables

Use `.env.example` as a guide and create your local `.env` file.

Example development configuration:

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
AFRICASTALKING_API_KEY=your_africas_talking_key
AFRICASTALKING_SMS_SENDER_ID=
```

> **Never commit real API keys, passwords, or production credentials to GitHub.**

---

# 🗄 Database Setup

Move into the backend:

```bash
cd backend
```

Apply migrations:

```bash
python manage.py migrate
```

Check Django:

```bash
python manage.py check
```

---

# 📖 Import the Constitution

Make sure the Constitution PDF exists under:

```text
legal_sources/uganda_constitution_2023.pdf
```

Then from the `backend` directory run:

```bash
python manage.py import_constitution \
  --pdf ../legal_sources/uganda_constitution_2023.pdf
```

The command validates and imports the document into the legal knowledge database.

---

# ▶️ Run the Backend

From:

```text
Sauti-Yo/backend
```

run:

```bash
python manage.py runserver
```

The backend development server runs at:

```text
http://127.0.0.1:8000/
```

API endpoints are available under `/api/`.

---

# 💻 Run the Frontend

Open another terminal and run:

```bash
cd ~/Projects/Sauti-Yo/frontend
npm install
npm run dev
```

The frontend development server normally runs at:

```text
http://localhost:5173/
```

During local development, frontend API requests can be proxied to the Django backend.

---

# 🔌 Important API Routes

Examples of API routes used by the platform include:

```text
/api/rights/
/api/rights/analyse/
/api/support/
/api/channels/sms/
/api/channels/ussd/
/api/channels/voice/
/api/chat/
/api/partners/
/api/referrals/
```

---

# 🧪 Testing

## Django system check

```bash
cd backend
python manage.py check
```

## Check migrations

```bash
python manage.py makemigrations --check --dry-run
```

## Run backend tests

```bash
python manage.py test
```

## Run channel-specific tests

SMS:

```bash
python manage.py test apps.channels.sms
```

USSD:

```bash
python manage.py test apps.channels.ussd
```

Voice:

```bash
python manage.py test apps.channels.voice
```

Chat:

```bash
python manage.py test apps.chat
```

---

# 🏗 Frontend Production Build

From the frontend directory:

```bash
cd frontend
npm run build
```

The TypeScript compiler and Vite production build should complete successfully before deployment.

---

# 🔐 Safety and Legal Information

Sauti Yo provides **legal information and practical guidance**.

It is not a substitute for:

- Emergency services
- A qualified lawyer
- Individual legal representation
- Professional advice based on the full facts of a person's case

Safety-critical information should be carefully verified before production deployment.

Support-service names and telephone numbers should also be verified before being presented to users.

Translated legal and safety content should be reviewed by qualified language and legal reviewers before being treated as final production content.

---

# ⚠️ AI Safety

AI is used as an interface to verified information rather than as the authoritative source of Ugandan law.

The legal assistant is designed to:

- Ground legal claims in supplied legal material
- Avoid inventing laws or constitutional provisions
- Preserve constitutional Article numbers
- Preserve supplied support contacts
- Avoid changing safety-critical guidance
- Clearly indicate when there is not enough verified information
- Fall back safely when AI services are unavailable

---

# 🚢 Deployment Notes

Having SMS, USSD, and Voice code in the repository does **not automatically mean those channels are live on a mobile network**.

Production deployment requires:

- Valid provider credentials
- Publicly accessible HTTPS webhook URLs
- Africa's Talking or other provider configuration
- Correct callback URLs
- Production environment variables
- Database configuration
- End-to-end telecom testing

Each channel should be tested using the intended production or sandbox provider before launch.

---

# 🎯 Current MVP Priorities

The current Sauti Yo MVP focuses on:

1. Stable Rights-to-Action web journeys
2. Reliable SMS access
3. Reliable USSD feature-phone access
4. Safe high-risk and emergency flows
5. Voice-channel integration
6. Grounded legal chatbot responses
7. Verified legal information
8. Verified multilingual content
9. Support and referral pathways
10. End-to-end deployment testing

---

# 🔮 Future Improvements

Possible future improvements include:

- Additional legal documents
- Expanded legal-topic coverage
- More verified multilingual content
- Multilingual web interface
- Improved legal-information retrieval
- Expanded referral networks
- Partner dashboards
- Usage analytics
- Additional accessibility improvements
- Production telecom integration
- More advanced AI-assisted navigation

---

# 🤝 Contributing

Contributors should work on focused feature branches and open pull requests into `main`.

Before opening or merging a pull request, run the relevant checks.

Backend:

```bash
cd backend

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Frontend:

```bash
cd frontend
npm run build
```

Git:

```bash
git diff --check
git status
```

Avoid committing:

- `.env`
- API keys
- Passwords
- Local database credentials
- Virtual environments
- Generated secrets

---

# 📄 License

See the `LICENSE` file in this repository.

---

## Sauti Yo

**Know your rights. Understand your options. Take the next step.**