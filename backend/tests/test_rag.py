from app.rag.retriever import HandbookRetriever

def test_handbook_answers_have_page_numbers():
    result = HandbookRetriever().search("How often are performance reviews conducted?")
    assert result and result[0].page == 4

def test_out_of_scope_is_empty():
    assert HandbookRetriever().search("What is the capital of France?") == []

