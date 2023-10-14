# Load a model from an artifact, and then server, logging the results to a streamtable

import os
import sys
from contextlib import asynccontextmanager

from pydantic import BaseModel
import weave
from weave.monitoring import StreamTable
from fastapi import FastAPI


model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model

    if os.environ.get("MODEL_REF") is None:
        print("Must provide MODEL_REF via env var")
        print(
            "MODEL_REF is of the form 'wandb-artifact:///<entity>/<project>/<objectName>:<objectVersion/obj"
        )
        sys.exit(1)

    model_uri = os.environ["MODEL_REF"]
    model_ref = weave.ref(model_uri)
    model = model_ref.get()
    project = (
        model_ref.artifact.uri_obj.entity_name
        + "/"
        + model_ref.artifact.uri_obj.project_name
    )

    weave.init(project)
    print("INITED")

    yield


app = FastAPI(docs_url="/", lifespan=lifespan)


class Item(BaseModel):
    example: str


@app.post("/predict")
def predict(item: Item):
    result = model.predict(item.example)
    record = {
        "model": model,
        "example": item.example,
        "result": result,
    }
    return {"prediction": result}
