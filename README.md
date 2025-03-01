# Killer App

A visualization tool for tracking "killer" targets in a game.

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

## Features

- Visualize killer targets as a directed graph
- Search for individuals by name or information
- Edit individual information directly in the app
- Dark mode toggle
- Special filters for specific groups (e.g., 5A filter)
- Track installation IDs and user logins

## Database Structure

This application uses Supabase with the following tables:
- `individus`: Stores individual players and their targets
- `settings`: Stores application settings like password
- `installations`: Tracks installations of the app
- `log`: Logs user actions for auditing

## Requirements

- Python 3.6+
- Supabase account with properly configured tables
- Dependencies listed in requirements.txt