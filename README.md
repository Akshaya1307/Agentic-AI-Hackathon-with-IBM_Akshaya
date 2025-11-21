### **WorkBuddy – Unified HR & IT Copilot Powered by IBM watsonx Orchestrate**

---

## 🚀 Overview

**WorkBuddy** is an AI-driven Employee Support Copilot designed to unify HR, IT, and Onboarding workflows inside organizations.
It uses natural language interaction and *agentic workflow simulation* to demonstrate how **IBM watsonx Orchestrate** can coordinate multi-step tasks and automated workflows across departments.

This project was developed for the **IBM Agentic AI Hackathon**, showcasing orchestration, multi-agent logic, and workflow automation in a clean, interactive UI.

---

## 💡 Key Capabilities

WorkBuddy helps employees complete key tasks instantly using conversational prompts:

### 🟣 **HR Agent**

* Check leave balance
* Retrieve HR policy summaries
* Guide employees for leave planning

### 🔵 **IT Agent**

* Create access request tickets (Salesforce, Jira, VPN, etc.)
* Simulated manager approval
* Simulated access granting
* Ticket status updates

### 🟢 **Onboarding Agent**

* Multi-step onboarding workflow
* HR profile creation
* Laptop & VPN request
* Tool access checklist
* Manager intro meeting scheduling

### 🤖 **General Assistant**

* Handles fallback queries
* Guides users on available tasks

---

## 🧠 **How IBM watsonx Orchestrate Fits In**

In a real enterprise environment:

* Each action (skill) would be exposed via APIs:

  * `CheckLeaveBalance`
  * `CreateAccessRequest`
  * `ApproveAccessRequest`
  * `StartOnboarding`
  * `OnboardingStep`

* **IBM watsonx Orchestrate** would:

  * Detect intent
  * Choose the correct digital skills
  * Execute them in sequence
  * Handle approvals
  * Maintain workflow context
  * Update logs and status

This prototype **simulates that exact orchestration** using:

* Multi-agent skill routing
* Workflow logs
* Multi-step onboarding workflow
* Manager approval automation

---

## 🏗️ Architecture

```
User (Chat UI)
        |
        ▼
WorkBuddy Router (Intent Detection)
        |
        ▼
┌───────────────────────────┐
│  Multi-Agent Skill Engine │
├──────────┬────────┬───────┤
│ HR Agent │ IT Agent │ Onboarding Agent │
└──────────┴────────┴────────────────────┘
        |
        ▼
 Simulated APIs / Workflows / Logs
```

---

## 🎨 Tech Stack

| Layer                       | Technology                                |
| --------------------------- | ----------------------------------------- |
| **Frontend UI**             | Streamlit                                 |
| **Backend Logic**           | Python (agents, skills, workflows)        |
| **Simulation Engine**       | Workflow logs + multi-step orchestration  |
| **Conceptual IBM Services** | watsonx Orchestrate, watsonx.ai, Cloudant |

---

## 📁 Project Structure

```
WorkBuddy/
│
├── app.py               # Streamlit UI (Chat + Dashboard)
├── backend.py           # Agents, skills, workflows, logs
├── README.md
└── requirements.txt
```

---

## ▶️ Run the App

### Install dependencies:

```
pip install -r requirements.txt
```

### Run Streamlit:

```
streamlit run app.py
```

Your browser will open WorkBuddy at:

```
http://localhost:8501
```

---

## 💬 Example Interactions

### 🟣 HR Query

**You:** How many casual leaves do I have?
**WorkBuddy:** HR Agent → “You have 4 casual leave days remaining.”

---

### 🔵 IT Access Request

**You:** I need Salesforce access.
**WorkBuddy:**

* Creates ticket
* Simulates manager approval
* Grants access
* Logs steps

---

### 🟢 Onboarding Workflow

**You:** Start onboarding a new analyst.
**WorkBuddy:**

* Starts multi-step onboarding
* Logs each step
* Shows status on dashboard

---

## 📊 Dashboard Features

* All IT requests
* Onboarding workflows
* Full workflow log list (simulating Orchestrate trace)
* Timestamped skill execution entries
* Agent-wise activity

---

## 📝 Workflow Log Example

```
[13:14:21] IT Agent
Skill: CreateAccessRequest
Status: Created
Ref: TKT-91C4A5
Details: Tool: Salesforce
```

```
[13:14:23] Manager Agent
Skill: ApproveAccessRequest
Status: Approved
Ref: TKT-91C4A5
Details: Auto-approved
```

```
[13:14:24] IT Agent
Skill: GrantAccess
Status: Completed
Ref: TKT-91C4A5
Details: Access granted
```

---

## ⭐ Why This Project Stands Out

* Multi-agent design
* Orchestrated workflows
* Realistic approval simulation
* Stepwise onboarding workflow
* Professional UI
* Dashboard + logs
* Clear IBM watsonx Orchestrate mapping
* Enterprise tone and structure

This is not another “chatbot.”
It is a **full HR + IT + Onboarding Copilot**.

---

## 👤 Author

**Naga Akshaya Boyidi – IBM Agentic AI Hackathon 2025**
