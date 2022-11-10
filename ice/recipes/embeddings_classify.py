import numpy as np

from ice.agents.ought_inference import OughtInferenceAgent
from ice.recipe import recipe

DOCUMENTS = [
    "Hello my name is Bob",
    "Hello my name is Alice",
    "Hello my name is Dave",
]

IRRELEVANT_DOCUMENTS = [
    "Do you like ice cream?",
    "Do you like chocolate?",
]


async def classify_documents(
    document: str = "My name is Bob",
    relevant_documents: list[str] = DOCUMENTS,
    irrelevant_documents: list[str] = IRRELEVANT_DOCUMENTS,
    alpha: float = 0.5,  # Higher means better precision, lower means better recall
    engine: str = "scibert",
) -> bool:
    agent = OughtInferenceAgent(engine=engine)
    embeddings_list = await agent.embeddings(
        documents=[document] + relevant_documents + irrelevant_documents,
    )
    embeddings = np.array(embeddings_list)

    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    document_embedding = embeddings[0]
    relevant_embeddings = embeddings[1 : len(relevant_documents) + 1]
    irrelevant_embeddings = embeddings[len(relevant_documents) + 1 :]

    upper_threshold = (relevant_embeddings @ relevant_embeddings.T).flatten().mean()

    lower_threshold = (relevant_embeddings @ irrelevant_embeddings.T).flatten().mean()

    threshold = lower_threshold + alpha * (upper_threshold - lower_threshold)

    similarity = (document_embedding @ relevant_embeddings.T).flatten().mean()

    return similarity > threshold


recipe.main(classify_documents)
