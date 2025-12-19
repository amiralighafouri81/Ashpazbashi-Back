The main server for the chroma vector database, containing the recipes and allowing for various searching.

The server has two endpoints:

## ```http://0.0.0.0:8324/insert```
 - Which accepts this body as input:
```
   {
    "recipes": [ {recipe items (available in data-insertion/ directory under Ashpazyar-data.jsonl)} ]
   }
```
 - And a Bearer token for authorization (defined in .env file) 



## ```http://0.0.0.0:8324/search```
 - Which accepts this body as input:

 - searching for the foods by foodname:
```
  {
    "query": "کتلت", 
    "include_ingredients": [],
    "limit": 10
  }
```

 - searching for the foods by ingredients:
```
  {
    "query": "", 
    "include_ingredients": ["تخم مرغ", "سیب زمینی"],
    "limit": 10
  }
```
 - hybrid search:
 ```
  {
    "query": "کتلت", 
    "include_ingredients": ["تخم مرغ", "سیب زمینی"],
    "limit": 10
  }
  ```
 - And a Bearer token for authorization (defined in .env file)

You also need a connection to the internet and an OpenRouter API key for the embeddings.

## How to build?
 - Run the dockerfile with this command: ```sudo docker build -t recipe-rag-server .``` where dockerfile exists.
 - Wait until the image is built.
 - Run a container with this command: ```sudo docker run --name recipe-server -p 8324:8324 --env-file .env -v $(pwd)/chroma_db:/app/chroma_db recipe-rag-server```
 - When built, run the code from ```data-insertion``` directory in the repository to insert the initial data.
 - After full insertion, call the endpoint for easy searching. 
