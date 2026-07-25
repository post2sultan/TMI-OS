from app.services.extraction.manager import extraction_manager


url = "https://news.microsoft.com/"

result = extraction_manager.extract(url)

print("=" * 80)
print("SUCCESS:", result.success)
print("EXTRACTOR:", result.extractor)
print("WORDS:", result.word_count)
print("ERROR:", result.error)
print("=" * 80)
print(result.content[:2000])
print("=" * 80)