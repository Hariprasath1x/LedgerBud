"""ETL package for statement extraction, transformation, and loading."""

# NOTE: The legacy IngestionPipeline in pipeline.py depends on Flask extensions.
# The FastAPI import service (import_service.py) imports directly from
# extractor, transformer.normalizer, transformer.deduplicator, and
# transformer.merchant_resolver — bypassing this module.
