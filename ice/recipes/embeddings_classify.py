import numpy as np
from typing import Any

from ice.agents.ought_inference import OughtInferenceAgent
from ice.recipe import recipe
from structlog import get_logger

DOCUMENTS = [
    "Hello my name is Bob",
    "Hello my name is Alice",
    "Hello my name is Dave",
]

IRRELEVANT_DOCUMENTS = [
    "Do you like ice cream?",
    "Do you like chocolate?",
]

log = get_logger()

def batch_generator(l: list[Any], batch_size: int = 16):
    for i in range(0, len(l), batch_size):
        yield l[i : i + batch_size]

async def classify_documents(
    documents: list[str] = ["My name is Bob"],
    relevant_documents: list[str] = DOCUMENTS,
    irrelevant_documents: list[str] = IRRELEVANT_DOCUMENTS,
    alpha: float = 0.5,  # Higher means better precision, lower means better recall
    engine: str = "scibert",
) -> list[bool]:
    agent = OughtInferenceAgent(engine=engine)

    log.info(
        "Calling Ought Inference API...",
        n_documents=(len(documents)+len(relevant_documents)+len(irrelevant_documents)),
    )

    embeddings_list = sum([
        await agent.embeddings(documents=batch) 
        for batch in batch_generator(documents + relevant_documents + irrelevant_documents)], 
    [])

    log.info("Computing cosine similarities...")

    embeddings = np.array(embeddings_list)

    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    documents_embedding = embeddings[: len(documents)]
    relevant_embeddings = embeddings[ len(documents) : len(documents) + len(relevant_documents)]
    irrelevant_embeddings = embeddings[ len(documents) + len(relevant_documents) :]

    upper_threshold = (relevant_embeddings @ relevant_embeddings.T).flatten().mean() if len(relevant_embeddings) > 0 else 0.2

    lower_threshold = (relevant_embeddings @ irrelevant_embeddings.T).flatten().mean() if len(irrelevant_documents) > 0 else -0.2

    threshold = lower_threshold + alpha * (upper_threshold - lower_threshold)

    classifications = []

    for document_embedding in documents_embedding:
        similarity = (document_embedding @ relevant_embeddings.T).flatten().mean()

        classifications.append(similarity > threshold)
    
    return classifications


recipe.main(classify_documents)
