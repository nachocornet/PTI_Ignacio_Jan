# SSI v2 - Self-Sovereign Identity Platform

**Status:** ✅ Production Ready | **Version:** 2.0 | **Tests:** All Passing

---

## 🚀 Quick Start (5 min)

### First Time Setup

```bash
cd /path/to/pti-v2/v2

# 1. Virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r config/requirements.txt

# 2. Auto setup (wallets, DB, contract)
python3 scripts/setup_complete.py
```

### Run Local Stack

```bash
python3 scripts/start_all.py
```

Opens automatically at: **http://127.0.0.1:8080/frontend_login.html**

**Default credentials:** `admin` / `admin123`

### Stop Everything

```bash
bash scripts/teardown.sh local
```

---

## 📋 Core Features

### Architecture
- **Frontend:** Modular UI (login portal, admin, verifier)
- **Backend:** Microservices (issuer_base + issuer_dni, verifier)
- **Blockchain:** Local dev + Sepolia testnet (configurable)
- **Database:** SQLite (local) + PostgreSQL (production)
- **CI/CD:** GitHub Actions automation

### Key Flows
1. **Login:** Session-based with localStorage (1hr TTL)
2. **Issue Credential:** Admin creates citizen → Issuer emits Over18Credential → Blockchain registration
3. **Verify:** Holder uploads wallet → Creates Verifiable Presentation → Verifies on-chain
4. **Revoke:** Issuer revokes credential on blockchain

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [docs/tutoriales/DESARROLLO_LOCAL.md](docs/tutoriales/DESARROLLO_LOCAL.md) | Local dev workflow, debugging |
| [docs/tutoriales/CI_CD_GITHUB_ACTIONS.md](docs/tutoriales/CI_CD_GITHUB_ACTIONS.md) | GitHub Actions setup |
| [docs/tutoriales/TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md) | Common issues & fixes |
| [docs/tutoriales/TESTNET_QUICKSTART.md](docs/tutoriales/TESTNET_QUICKSTART.md) | Deploy to Sepolia |
| [docs/tutoriales/GUIA_FRONTEND.md](docs/tutoriales/GUIA_FRONTEND.md) | Frontend UX guide |
| [docs/operacion/GUIA_PASO_A_PRO.md](docs/operacion/GUIA_PASO_A_PRO.md) | Production (3-VM deploy) |
| [docs/referencia/GUIA_CODIGO_Y_CAMBIOS.md](docs/referencia/GUIA_CODIGO_Y_CAMBIOS.md) | Code structure & changes |

---

## 🏗️ Project Structure

```
v2/
├── services/
│   ├── issuer_base/              # Generic reusable issuer library
│   ├── issuer_dni/               # DNI-specific issuer (extends base)
│   └── verifier/                 # Credential verification
├── frontend/
│   ├── frontend_login.html       # Session login portal
│   ├── frontend_portal.html      # Central hub after login
│   ├── issuer_admin.html         # Admin: citizen CRUD
│   ├── issuer_dashboard.html     # Issue/revoke interface
│   ├── verifier_dashboard.html   # Verify presentations
│   └── frontend.variables.js     # Auto-generated config
├── shared/
│   ├── blockchain_client.py      # Web3 wrapper
│   └── settings.py               # Centralized config
├── config/
│   ├── requirements.txt           # Python dependencies
│   ├── .env.complete.example      # All env vars documented
│   └── compose_vms/               # Docker for production
├── deployments/                   # Wallets, ABIs, contracts
├── scripts/
│   ├── setup_complete.py          # First-time setup
│   ├── start_all.py               # Run all local services
│   ├── deploy_vms.sh              # Deploy to production
│   └── seed_db.py                 # Initialize DB
└── tests/
    ├── test_issuer.py             # Issuer API tests
    ├── test_verifier.py           # Verifier tests
    └── test_e2e.py                # End-to-end tests
```

---

## 🧪 Testing

### Run All Tests

```bash
cd v2
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -v
```

**Expected:** 27+ tests passing ✅

### Test Coverage

- ✅ Admin citizen CRUD (DNI validation: format, checksum, age >= 18)
- ✅ Issue Over18Credential with blockchain registration
- ✅ Verify presentation with on-chain checks
- ✅ Revoke credential and validate rejection
- ✅ Authentication (Basic Auth + Session-based login)
- ✅ Error handling (400, 401, 403, 404, 409, 503)

---

## ⚙️ Configuration

### Environment Variables

All in `.env`. Full reference: [config/.env.complete.example](config/.env.complete.example)

**Key variables:**
```bash
SSI_BLOCKCHAIN_NETWORK=sepolia          # local | sepolia
SEPOLIA_RPC_URL=https://...             # Sepolia RPC
DATABASE_URL=postgresql://...           # Production DB
SSI_ADMIN_USER=admin                    # Admin login
SSI_ADMIN_PASSWORD=admin123             # Admin password
```

---

## 🚢 Deployment

### Local Development
```bash
python3 scripts/start_all.py
```

### Sepolia Testnet
```bash
export SEPOLIA_RPC_URL="https://..."
export DB_PASSWORD="..."
bash scripts/deploy_vms.sh
```

See [docs/operacion/GUIA_PASO_A_PRO.md](docs/operacion/GUIA_PASO_A_PRO.md) for production deployment.

---

## 🔑 Key Concepts

### Modular Issuer Architecture

- **issuer_base:** Generic credential infrastructure (auth, blockchain, DB)
- **issuer_dni:** DNI-specific validators + Over18Credential logic

Allows adding new issuer types without code duplication.

### Session Management

- Login creates session in browser localStorage
- TTL: 1 hour
- Pages validate session before rendering
- Logout clears session

### Blockchain Integration

- DID format: `did:ethr:0x<address>`
- On-chain: SetDidStatus, RegisterCredential, RevokeCredential
- Local dev mode supported

---

## ❓ Quick Help

**Q: Where are wallets?**  
A: `deployments/runtime/{issuer_wallet,wallet}.json`

**Q: Add a new citizen?**  
A: Login → Admin → Create (validates DNI format + age >= 18)

**Q: Verify credential?**  
A: Verifier → Upload wallet → Upload/paste VC → Verify

**Q: Troubleshoot?**  
A: [TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md)

---

## 📖 Next Steps

1. Run locally → `python3 scripts/start_all.py`
2. Test full flow → Create citizen → Issue → Verify
3. Read tutorials → Pick one from `docs/tutoriales/`
4. Deploy → See `GUIA_PASO_A_PRO.md`

---

**Last Updated:** April 29, 2026 | Modular Architecture Release
