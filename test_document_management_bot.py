import pytest
from document_management_bot1 import DocumentManagementBot

def test_create_document():
    bot = DocumentManagementBot()
    response = bot.create_document("Test Document")
    assert response == "Document 'Test Document' created successfully."
    assert "Test Document" in bot.list_documents()

def test_update_document():
    bot = DocumentManagementBot()
    bot.create_document("Test Document")
    response = bot.update_document("Test Document", "Updated Content")
    assert response == "Document 'Test Document' updated successfully."
    assert bot.get_document("Test Document") == "Updated Content"

def test_upload_document():
    bot = DocumentManagementBot()
    response = bot.upload_document("Uploaded Document", "This is the content of the uploaded document.")
    assert response == "Document 'Uploaded Document' uploaded successfully."
    assert "Uploaded Document" in bot.list_documents()
    assert bot.get_document("Uploaded Document") == "This is the content of the uploaded document."

def test_delete_document():
    bot = DocumentManagementBot()
    bot.create_document("Test Document")
    response = bot.delete_document("Test Document")
    assert response == "Document 'Test Document' deleted successfully."
    assert "Test Document" not in bot.list_documents()

def test_rename_document():
    bot = DocumentManagementBot()
    bot.create_document("Old Document")
    response = bot.rename_document("Old Document", "New Document")
    assert response == "Document 'Old Document' renamed to 'New Document' successfully."
    assert "New Document" in bot.list_documents()
    assert "Old Document" not in bot.list_documents()
