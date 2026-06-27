# NutriAI — Profile Service

The **Profile Service** manages user biometrics (height, weight, age), emergency contacts, blood types, dietary preferences, medical conditions, and food allergies.

---

## 🏗️ Core Role & Functionality
1. **Patient Profile Manager**: Exposes endpoints to create, fetch, and update basic demographic and biometric profiles.
2. **Medical History Registry**: Tracks dietary preferences and medical diagnoses in the database.
3. **Allergen Registry**: Tracks user food allergies, severity flags, and reaction logs.

---

## 🛠️ Technology Stack
* **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
* **ORM & DB Connection**: [SQLAlchemy](https://www.sqlalchemy.org/) & [Psycopg2](https://www.psycopg.org/)
* **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)

---

## ⚙️ Configuration & Environment Variables

Variables are configured in [app/config.py](file:///c:/Users/YASWANTH/cloudtrack_final/NutriAI-profile-service/app/config.py):

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./test.db` | PostgreSQL connection URL. |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | *Empty* | Azure Application Insights SDK telemetry connection. |

---

## 🗄️ Database Models

Model details are in [app/models.py](file:///c:/Users/YASWANTH/cloudtrack_final/NutriAI-profile-service/app/models.py):

* **User**: Base model storing email, username, full name, age, height, weight, auth type (`local` or `entra`), Entra Object ID (`entra_oid`), and role details.
* **PatientProfile**: Linked 1-to-1 with `User`. Holds list fields for medical conditions, dietary preferences, blood type, and emergency contacts.
* **FoodAllergy**: Linked many-to-1 with `User`. Tracks allergen name, severity (`mild`, `moderate`, `severe`), and notes.

---

## 🔌 API Endpoints Reference

All routes are declared in [app/routes.py](file:///c:/Users/YASWANTH/cloudtrack_final/NutriAI-profile-service/app/routes.py).

| HTTP Method | Route | Description | Auth Header Required |
| :--- | :--- | :--- | :--- |
| **GET** | `/profile` | Returns current user details, profile record, and allergy lists. | `X-User-ID` |
| **POST** | `/profile/update` | Updates user details (full name, age, weight, height). | `X-User-ID` |
| **POST** | `/profile/medical` | Updates medical conditions list, dietary preferences, blood type, and emergency contacts. | `X-User-ID` |
| **POST** | `/profile/allergy` | Appends a new allergen to the patient's allergy list. | `X-User-ID` |
| **DELETE** | `/profile/allergy/{allergy_id}`| Removes a food allergy record from the DB. | `X-User-ID` |

---

## 🔄 Integration & Routing

1. **Ingress Route**: Client web browsers send profile requests to `/api/profile/*`.
2. **API Gateway Service**: Verifies the JWT cookie and forwards requests to the Profile Service with the `X-User-ID` header.
3. **Database Sharing**: Writes details to the shared PostgreSQL instance. The Diet Service reads profile and allergy entries directly from this database during OpenAI diet generations.

---

## 🚀 CI/CD Pipeline
* Code triggers: [.github/workflows/cicd.yml](file:///c:/Users/YASWANTH/cloudtrack_final/NutriAI-profile-service/.github/workflows/cicd.yml).
* Uses reusable shared pipelines: format verification, unit testing, SonarQube quality gate and Snyk checks, Trivy container validation, push to ACR, and updates the manifests repository (`helm/nutriai/values-{env}.yaml`).

---

## 💻 Local Development

```bash
# Install packages
pip install -r requirements.txt

# Run profile service locally (starts on port 8006)
uvicorn app.main:app --port 8006 --reload
```
Access at `http://127.0.0.1:8006`.
