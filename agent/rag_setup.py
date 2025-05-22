from llama_index import VectorStoreIndex, SimpleDirectoryReader

def setup_rag_index(docs_path):
    documents = SimpleDirectoryReader(docs_path).load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index

def get_rag_retriever(index):
    return index.as_retriever()
