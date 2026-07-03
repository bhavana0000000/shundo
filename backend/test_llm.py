from app.agents.llm_client import get_llm

llm = get_llm()
response = llm.invoke("Say hello and confirm you're running on NVIDIA NIM.")
print(response.content)