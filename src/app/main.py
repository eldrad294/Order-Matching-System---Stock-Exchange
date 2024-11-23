from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def hello_world():
    """
    Test
    """
    return {"message": "Hello World"}