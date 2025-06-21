from core.utils import read_file

def explain_code(filepath):
    from core.agent_store import AGENT_MAP  # imported inside to avoid circular import
    code = read_file(filepath)
    agent = AGENT_MAP.get("explain")
    return agent.run(code) if agent else "Explainer agent not available."

def fix_code(filepath):
    from core.agent_store import AGENT_MAP  # imported inside to avoid circular import
    code = read_file(filepath)
    agent = AGENT_MAP.get("review")
    return agent.run(code) if agent else "Reviewer agent not available."

def generate_code(prompt_text):
    from core.agent_store import AGENT_MAP  # imported inside to avoid circular import
    agent = AGENT_MAP.get("nl_to_code") or AGENT_MAP.get("python")
    return agent.run(prompt_text) if agent else "Code generator agent not available."
