# 🤖 Groq LangChain Memory AI Assistant

A stunning **terminal-based AI assistant** built with [LangChain](https://www.langchain.com/) and the **Groq API**.  
It remembers past chats, manages meetings (add, show, delete), and talks naturally like ChatGPT — all locally in your terminal.

---

## 🚀 Features

✅ **Conversational Memory** — remembers your previous chats, even after restart  
✅ **Meeting Management** — add, show, and delete meetings using natural language  
✅ **Automatic Cleanup** — removes expired meetings after their scheduled time  
✅ **Persistent Storage** — chat history & meetings saved in JSON files  
✅ **Groq-Powered LLM** — ultra-fast responses using `langchain_groq`  
✅ **Beautiful Terminal UI** — built with the `rich` library for colored output  

---

## 🧠 Example Conversations

```bash
You: schedule a meeting at 8am for project discussion  
Assistant: ✅ Meeting added — “project discussion” at 08:00 AM

You: show my upcoming meetings  
Assistant: 📅 You have 1 meeting scheduled:
- Project Discussion — 08:00 AM, Today

You: delete my 8am meeting  
Assistant: 🗑️ Meeting “Project Discussion” deleted.

You: hi  
Assistant: Hey there! How can I help you today?
