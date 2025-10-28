"""
Groq Memory AI Assistant (LangChain + Groq API)
-------------------------------------------------
 Features:
 - Persistent memory (remembers chat & meetings across sessions)
 - Natural date/time parsing (e.g. "tomorrow 9am", "next Monday 3pm")
 - Understands multiple ways to say add/show/delete meetings
 - Auto-removes past meetings
 - Professional ChatGPT-like terminal UI
"""

# ================= IMPORTS =================
import os
import re
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from dateutil import parser as date_parser
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

# ================= SETUP =================
load_dotenv()
console = Console()

HISTORY_FILE = "chat_history.json"
MEETINGS_FILE = "meetings.json"

# ================= HELPERS =================
def load_json(file_path, default_value):
    """Load JSON file safely or return default."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return default_value


def save_json(file_path, data):
    """Save Python objects as JSON."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def typing_effect(text):
    """Simulate typing animation."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.015)
    print()


# ================= MEETING MANAGEMENT =================
def parse_natural_datetime(text):
    """Parse natural date/time phrases (e.g. 'tomorrow 3pm', 'next monday 10am')."""
    text = text.lower().strip()
    now = datetime.now()

    if "tomorrow" in text:
        base_date = now + timedelta(days=1)
        time_match = re.search(r"\d{1,2}(:\d{2})?\s?(am|pm)?", text)
        time_str = time_match.group() if time_match else "9am"
        dt = date_parser.parse(f"{base_date.strftime('%Y-%m-%d')} {time_str}")
        return dt.strftime("%Y-%m-%d %H:%M")

    days_map = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days_map):
        if f"next {day}" in text:
            days_ahead = (i - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            base_date = now + timedelta(days=days_ahead)
            time_match = re.search(r"\d{1,2}(:\d{2})?\s?(am|pm)?", text)
            time_str = time_match.group() if time_match else "9am"
            dt = date_parser.parse(f"{base_date.strftime('%Y-%m-%d')} {time_str}")
            return dt.strftime("%Y-%m-%d %H:%M")

    # Fallback: parse whatever format user gave
    try:
        dt = date_parser.parse(text, fuzzy=True, default=now)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None


def cleanup_old_meetings():
    """Remove meetings that are already past."""
    now = datetime.now()
    meetings = load_json(MEETINGS_FILE, [])
    active = [m for m in meetings if datetime.strptime(m["time"], "%Y-%m-%d %H:%M") > now]
    save_json(MEETINGS_FILE, active)


def add_meeting(title, time_str):
    """Add a meeting and store it persistently."""
    meetings = load_json(MEETINGS_FILE, [])
    meetings.append({"title": title, "time": time_str})
    save_json(MEETINGS_FILE, meetings)
    return f"Meeting '{title}' scheduled for {time_str}."


def show_meetings():
    """Display all upcoming meetings."""
    meetings = load_json(MEETINGS_FILE, [])
    if not meetings:
        return "No upcoming meetings found."
    result = " Upcoming Meetings:\n"
    for m in meetings:
        result += f"- {m['title']} at {m['time']}\n"
    return result


def delete_meeting(title):
    """Delete a meeting by its title."""
    meetings = load_json(MEETINGS_FILE, [])
    updated = [m for m in meetings if m["title"].lower() != title.lower()]
    save_json(MEETINGS_FILE, updated)
    return f"Deleted meeting '{title}'." if len(updated) < len(meetings) else "Meeting not found."


# ================= LLM SETUP =================
llm = ChatGroq(
    temperature=0.7,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70B-versatile"
)


# ================= CHAT LOGIC =================
def chat_with_ai(user_input):
    """Handle user input and route to meeting or general chat."""
    history = load_json(HISTORY_FILE, [])
    messages = [
        HumanMessage(content=m["content"]) if m["type"] == "human" else AIMessage(content=m["content"])
        for m in history
    ]

    text = user_input.lower()

    # ---------- Keyword sets ----------
    add_keywords = ["add meeting", "schedule", "make meeting", "create meeting", "new meeting"]
    show_keywords = ["show meetings", "list meetings", "upcoming meetings", "view meetings", "any meetings"]
    delete_keywords = ["delete meeting", "remove meeting", "cancel meeting"]

    # ---------- Add Meeting ----------
    if any(k in text for k in add_keywords):
        try:
            if " at " in text:
                parts = user_input.split(" at ")
                title = parts[0]
                for kw in add_keywords:
                    title = title.replace(kw, "")
                title = title.strip()
                time_text = parts[1].strip()

                parsed_time = parse_natural_datetime(time_text)
                if parsed_time:
                    ai_reply = add_meeting(title, parsed_time)
                else:
                    ai_reply = "I couldn’t understand the time. Try 'schedule meeting team sync tomorrow 3pm'."
            else:
                ai_reply = "Please provide a time, e.g. 'schedule meeting with HR at 2pm'."
        except Exception:
            ai_reply = "Couldn't parse meeting details properly."
    # ---------- Show Meetings ----------
    elif any(k in text for k in show_keywords):
        ai_reply = show_meetings()
    # ---------- Delete Meeting ----------
    elif any(k in text for k in delete_keywords):
        title = user_input
        for kw in delete_keywords:
            title = title.replace(kw, "")
        title = title.strip()
        ai_reply = delete_meeting(title)
    # ---------- Regular Chat ----------
    else:
        messages.append(HumanMessage(content=user_input))
        response = llm.invoke(messages)
        ai_reply = response.content
        messages.append(AIMessage(content=ai_reply))

    # Save conversation history
    save_json(
        HISTORY_FILE,
        [{"type": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content} for m in messages]
    )
    return ai_reply


# ================= MAIN LOOP =================
def main():
    """Main terminal loop."""
    console.print(Panel("Office AI Assistant", style="bold blue"))
    print("Type 'exit' to quit.\n")

    cleanup_old_meetings()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            console.print(Panel("Goodbye! Have a nice day.", style="green"))
            break

        reply = chat_with_ai(user_input)
        print("Assistant: ", end="")
        typing_effect(reply)
        print()


# ================= ENTRY =================
if __name__ == "__main__":
    main()
