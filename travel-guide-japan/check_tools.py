import os
from app.agent import root_agent, weather_agent, search_agent

print("=== Japan Guide (Root Agent) Tools ===")
print("Tools:", [t.name if hasattr(t, "name") else str(t) for t in root_agent.tools])
print(
    "Sub-agents:",
    [sa.name for sa in root_agent.sub_agents]
    if hasattr(root_agent, "sub_agents")
    else "None",
)

print("\n=== Weather Agent Tools ===")
print("Tools:", [t.name if hasattr(t, "name") else str(t) for t in weather_agent.tools])

print("\n=== Search Agent Tools ===")
print("Tools:", [t.name if hasattr(t, "name") else str(t) for t in search_agent.tools])
