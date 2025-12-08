from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router as api_router

app = FastAPI(
    title="Analyseur Syntaxique API",
    description="API pour l'analyseur syntaxique et interpréteur",
    version="1.0.0"
)

# Configuration CORS (Cross-Origin Resource Sharing)
# Permet au frontend Angular (port 4200) de communiquer avec ce backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Serveur de développement Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Analyseur Syntaxique API is running"}

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur avec rechargement automatique en cas de modif du code
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
