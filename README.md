# Killer App

A desktop application for tracking "killer" game targets. Players are stored in a Supabase database and visualized as kill chains arranged in a circle, with arrows pointing from each player to their target.

The user interface is in French.

## Features

- Password-protected login (password stored in the Supabase `settings` table)
- Visualize killer chains as a directed graph laid out in a circle
- Create individuals and assign their kill target by name (missing targets are created automatically)
- Delete individuals; their killer is re-linked to their victim
- Search for individuals by name or by information content
- Edit an individual's name, info, and kill target via a click popup
- Special filters for specific groups (e.g., 5A filter)
- Zoom with the mouse wheel and pan by dragging the canvas
- Dark mode toggle and adjustable name font size (Options menu)
- Track installation IDs and usernames

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your Supabase credentials:
   ```
   SUPABASE_URL="your_supabase_url_here"
   SUPABASE_KEY="your_supabase_key_here"
   ```
4. Run the application:
   ```
   python main.py
   ```

The application exits at startup if `SUPABASE_URL` or `SUPABASE_KEY` are missing.

## Build a Windows Executable

A PyInstaller spec file is included (`main.spec`). To build `dist/Killer.exe`:

```
pip install pyinstaller
pyinstaller main.spec
```

## Database Structure

This application uses Supabase with the following tables:
- `individus`: Stores individual players and their targets (`nom`, `info`, `kill`)
- `settings`: Stores application settings like password
- `installations`: Tracks installations of the app (`install_id`, `username`)
- `log`: Logs user actions for auditing

## Tech Stack

- Python 3 + Tkinter (GUI)
- [Supabase](https://supabase.com/) client (`supabase`) for storage and authentication
- `python-dotenv` for environment configuration
- `appdirs` for storing the installation ID
- PyInstaller for packaging into a Windows executable

## Requirements

- Python 3.6+
- A Supabase project with properly configured tables
- Dependencies listed in requirements.txt
