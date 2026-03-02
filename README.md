# 🎮 E-Sports Tournament Management System

A robust, Django-powered web application designed for organizing, managing, and tracking E-Sports tournaments with ease. This platform provides a comprehensive suite of tools for administrators, tournament organizers, and players.

## 🚀 Key Features

### 👤 User Roles & Management
- **Administrator**: Complete control over the platform, users, and content.
- **Tournament Organizer (TC)**: Create and manage tournaments, verify registrations, and schedule matches.
- **Players**: Create profiles, form or join teams, and register for tournaments.

### 🏆 Tournament System
- **Dynamic Creation**: Organizers can set up tournaments with specific games, team sizes, and prize pools.
- **Registration Workflow**: Teams can register for upcoming tournaments, with organizers managing approvals and payment statuses.
- **Status Tracking**: Visual indicators for tournament states: Upcoming, Ongoing, and Completed.

### 👥 Team & Player Management
- **Player Profiles**: Custom gamer tags, contact details, and game preferences.
- **Team Creation**: Players can request to form teams, subject to approval.
- **Roster Management**: Captains can manage their team members and roles.

### ⚔️ Match Scheduling & Results
- **Automated Scheduling**: Easily set up matchups between registered teams.
- **Round Management**: Organize matches by rounds (e.g., Quarter-Finals, Finals).
- **Score Tracking**: Real-time score updates and winner declarations.

### 🔔 Communication & Feedback
- **Notifications**: Stay updated with in-app notifications for tournament status and match schedules.
- **Feedback Loop**: Players can provide ratings and feedback on tournaments, with direct admin replies.

## 🛠️ Technology Stack
- **Backend**: Python 3.x, Django 5.x
- **Database**: SQLite (Default)
- **Frontend**: HTML5, Vanilla CSS, JavaScript
- **Others**: Pillow (Image handling), NLTK (Text processing)

## 📁 Project Structure
```text
E_sports/
├── game/                   # Django Project Root
│   ├── manage.py           # Django CLI
│   ├── myapp/              # Core Application Logic (Models, Views, Templates)
│   ├── static/             # CSS, JavaScript, and Images
│   └── templates/          # HTML Templates
├── requirements.txt        # Python Dependencies
└── README.md               # Project Documentation
```

## ⚙️ Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd E-Sports-Tournament
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   python game/manage.py migrate
   ```

5. **Start Development Server**
   ```bash
   python game/manage.py runserver
   ```
   Access the app at `http://127.0.0.1:8000/`

---
*Developed with ❤️ for the E-Sports Community.*

