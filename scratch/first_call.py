from app.llm import get_llm

llm = get_llm()
response = llm.invoke("In one sentence, what is a database index")
print(response.content)

