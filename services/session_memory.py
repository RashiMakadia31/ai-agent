from collections import deque

class SessionMemory:
    def __init__(self, max_length=10):
        self.memory = deque(maxlen=max_length)

    def add_message(self, role: str, content: str):
        self.memory.append({"role": role, "content": content})

    def get_memory(self):
        return list(self.memory)

    def clear_memory(self):
        self.memory.clear()