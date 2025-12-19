import os, json
from typing import Optional, List, Any, Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# LangChain Imports
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

# --- Configuration ---
CHROMA_PATH = "./chroma_db"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHROMA_ACCESS_TOKEN = os.getenv("CHROMA_ACCESS_TOKEN")

# OpenRouter utilizes OpenAI's client structure. 
# We typically use 'text-embedding-3-small' or 'text-embedding-ada-002' if mapped,
# or a specific model provided by OpenRouter.
EMBEDDINGS = OpenAIEmbeddings(
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    model="text-embedding-3-small", # Ensure this model is supported by your OpenRouter tier
    check_embedding_ctx_length=False
)

app = FastAPI(
    title="Recipe RAG Server",
    description="Vector Search for Persian Recipes using ChromaDB"
)

auth_scheme = HTTPBearer()

# --- Authentication ---
def authenticate(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if credentials.credentials != CHROMA_ACCESS_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials

# --- Pydantic Models for Input ---

class RecipeInput(BaseModel):
    foodname: str
    ingredients: Dict[str, str] # The raw ingredients dict
    canonical: List[str]        # The cleaned list for search/filtering
    recipe: List[str]           # Steps
    calory: Optional[str] = ""
    taken_time: Optional[List[str]] = []
    images: List[str] = []
    index: float
    questions: Dict[str, str]

class InsertRequest(BaseModel):
    recipes: List[RecipeInput]

class SearchRequest(BaseModel):
    query: str
    # Optional: Filter by specific ingredients (must contain ALL of these)
    include_ingredients: Optional[List[str]] = None 
    # Optional: Filter by max time (needs your time parsing logic, simplified here)
    limit: int = 3

# --- Core Logic ---

def process_recipe_to_document(recipe: RecipeInput) -> Document:
    """
    Converts a structured Recipe object into a Vector Document.
    """
    # 1. Create the Semantic Content (The part the AI searches)
    ingredients_str = json.dumps(recipe.ingredients, ensure_ascii=False).removeprefix("{").removesuffix("}")
    questions_str = json.dumps(recipe.questions, ensure_ascii=False).removeprefix("{").removesuffix("}")
    instructions_str = " ".join(recipe.recipe)
    
    page_content = f"""
    نام غذا: {recipe.foodname}
    دستور پخت: {instructions_str}
    """

    # 2. Prepare Metadata (The part we filter by)
    
    # Handle Images: Join with '||' to split later
    images_str = "||".join(recipe.images) if recipe.images else ""
    canonical_str = ",".join(recipe.canonical)

    
    # Handle Taken Time (it's a list in your JSON, take first item or join)
    time_str = recipe.taken_time[0] if recipe.taken_time else ""

    metadata = {
        "foodname": recipe.foodname,
        "calory": recipe.calory if recipe.calory else "Unknown",
        "index": recipe.index,
        "images": images_str,
        "canonical": canonical_str, 
        "taken_time": time_str,
        "detailed_ingredients": ingredients_str,
        "questions": questions_str
    }

    return Document(page_content=page_content, metadata=metadata)

def get_db():
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=EMBEDDINGS)

def has_all_ingredients(canonical_str: str, ingredients: list[str]) -> bool:
    canonical_list = [c.strip() for c in canonical_str.split(",")]
    return all(ing in canonical_list for ing in ingredients)


# --- Endpoints ---

@app.post("/insert")
async def insert_recipes(request: InsertRequest, auth: HTTPAuthorizationCredentials = Depends(authenticate)):
    if not request.recipes:
        raise HTTPException(status_code=400, detail="No recipes provided")

    documents = [process_recipe_to_document(r) for r in request.recipes]
    ids = [str(uuid4()) for _ in range(len(documents))]

    try:
        db = get_db()
        # Add in batches is usually safer for large data, but fine for <1000 at once
        db.add_documents(documents=documents, ids=ids)
        return {"message": f"Successfully inserted {len(documents)} recipes."}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_recipes(request: SearchRequest, auth=Depends(authenticate)):
    db = get_db()

    try:

        if not request.query.strip():
            # CASE A: No text query, just filter by ingredients
            existing_data = db.get(limit=330) # Adjust limit based on DB size
            
            results = []
            for i in range(len(existing_data['documents'])):
                doc = Document(
                    page_content=existing_data['documents'][i],
                    metadata=existing_data['metadatas'][i]
                )
                results.append((doc, 0.0)) # Score is 0.0 because there is no similarity
        else:
            # CASE B: Standard Vector Search
            results = db.similarity_search_with_score(
                query=request.query,
                k=request.limit * 10 # Get a larger pool to allow for filtering
            )

        filtered_results = []

        for doc, score in results:
            if request.include_ingredients:
                canonical = doc.metadata.get("canonical", "")
                if not has_all_ingredients(canonical, request.include_ingredients):
                    continue

            filtered_results.append((doc, score))

        filtered_results = filtered_results[:request.limit]

        response = []

        for doc, score in results:
            canonical_str = doc.metadata.get("canonical", "")
            canonical_list = [c.strip() for c in canonical_str.split(",") if c.strip()]

            if request.include_ingredients:
                if not all(ing in canonical_list for ing in request.include_ingredients):
                    continue

            images_list = [
                img for img in doc.metadata.get("images", "").split("||") if img
            ]

            ingredients_dict = json.loads("{" + doc.metadata.get("detailed_ingredients") + "}")

            response.append({
                "score": score,
                "foodname": doc.metadata.get("foodname"),
                "ingredients": ingredients_dict,
                "images": images_list,
                "calory": doc.metadata.get("calory"),
                "recipe": doc.page_content,
                "questions": doc.metadata.get("questions")
            })

            if len(response) >= request.limit:
                break

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8324)