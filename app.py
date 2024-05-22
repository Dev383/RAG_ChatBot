from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import HuggingFaceHub
import pinecone
from dotenv import load_dotenv
import os


class ChatBot:
    load_dotenv()
    loader = TextLoader("docs/aap_delhi.txt")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
    docs = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings()

    pinecone.init(
        api_key="6a34859c-5085-406c-9973-55d6c8c22ad9", environment="gcp-starter"
    )

    index_name = "langchain-demo"

    if index_name not in pinecone.list_indexes():
        pinecone.create_index(name=index_name, metric="cosine", dimension=768)
        docsearch = Pinecone.from_documents(docs, embeddings, index_name=index_name)
    else:
        docsearch = Pinecone.from_existing_index(index_name, embeddings)

    repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    llm = HuggingFaceHub(
        repo_id=repo_id,
        model_kwargs={"temperature": 0.8, "top_p": 0.8, "top_k": 50},
        huggingfacehub_api_token="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",
    )

    from langchain import PromptTemplate

    template = """
    You are a knowledgeable political analyst. Below is a question from a user who wants to understand more about the political party positions from their manifesto. Your role is to provide a factual, unbiased answer based on the provided political manifesto. If the information is not available in the manifesto, it's okay to say you don't know. Keep your answers precise and do not answer questions not related to politics.
    Context: {context}
    Query: {question}
    Answer:
  """

    prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    from langchain.schema.runnable import RunnablePassthrough
    from langchain.schema.output_parser import StrOutputParser

    rag_chain = (
        {"context": docsearch.as_retriever(), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
