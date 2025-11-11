import argparse
from typing import List
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from ..tools.db_vector_store import get_vector_store


def load_and_split_markdown(path: str) -> List[Document]:
    with open(path, "r") as f:
        markdown_text = f.read()

    # Split by headings so each chunk represents a topic/section
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
        ("#", "section"),
    ])
    docs = splitter.split_text(markdown_text)
    return [
        Document(
            page_content=d.page_content,
            metadata={**(d.metadata or {}), "source": path},
        )
        for d in docs
    ]


def build_index(markdown_path: str, collection_name: str = "docs") -> int:
    docs = load_and_split_markdown(markdown_path)
    vector_store = get_vector_store(collection_name=collection_name)
    if vector_store is None:
        raise RuntimeError("VECTOR_DB_URL is not set. Cannot connect to PGVector.")
    vector_store.add_documents(docs)
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Build vector index from a markdown file.")
    parser.add_argument("--path", required=True, help="Path to the markdown file")
    parser.add_argument("--collection", default="docs", help="Collection name")
    args = parser.parse_args()

    count = build_index(args.path, collection_name=args.collection)
    print(f"Indexed {count} chunks into collection '{args.collection}'.")


if __name__ == "__main__":
    main()


