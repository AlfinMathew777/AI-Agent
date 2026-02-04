"""ChromaDB utilities with safety checks and error handling."""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

CHROMA_AVAILABLE = False
chromadb = None

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB not installed - vector search will be unavailable")


class ChromaDBError(Exception):
    """Custom exception for ChromaDB operations"""
    pass


def initialize_chroma_client(
    persist_directory: str = "./chroma_db",
    max_retries: int = 3
) -> Optional[Any]:
    """
    Initialize ChromaDB client with safety checks.
    
    Args:
        persist_directory: Directory to store ChromaDB data
        max_retries: Maximum initialization attempts
    
    Returns:
        ChromaDB client or None if unavailable
    """
    if not CHROMA_AVAILABLE:
        logger.warning("ChromaDB is not available")
        return None
    
    for attempt in range(max_retries):
        try:
            # Create directory if it doesn't exist
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize client with persistence
            client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Test connection by listing collections
            client.list_collections()
            
            logger.info(f"ChromaDB initialized successfully at {persist_directory}")
            return client
        
        except Exception as e:
            logger.warning(
                f"ChromaDB initialization attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt == max_retries - 1:
                logger.error("ChromaDB initialization failed after all retries")
                return None
    
    return None


def health_check_chroma(client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Check ChromaDB health status.
    
    Args:
        client: ChromaDB client (will create if None)
    
    Returns:
        Dict with status and metadata
    """
    if not CHROMA_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "ChromaDB package not installed",
            "collections_count": 0
        }
    
    try:
        if client is None:
            client = initialize_chroma_client(max_retries=1)
        
        if client is None:
            return {
                "status": "unavailable",
                "message": "ChromaDB not initialized",
                "collections_count": 0
            }
        
        # Get collections
        collections = client.list_collections()
        
        return {
            "status": "healthy",
            "collections_count": len(collections),
            "collections": [col.name for col in collections],
            "message": "ChromaDB is healthy"
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "ChromaDB health check failed",
            "collections_count": 0
        }


def safe_get_or_create_collection(
    client: Any,
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    embedding_function: Optional[Any] = None
) -> Optional[Any]:
    """
    Safely get or create a ChromaDB collection.
    
    Args:
        client: ChromaDB client
        name: Collection name
        metadata: Optional collection metadata
        embedding_function: Optional embedding function
    
    Returns:
        Collection or None on error
    """
    if not client:
        logger.error("ChromaDB client is None")
        return None
    
    try:
        # Try to get existing collection
        collection = client.get_collection(
            name=name,
            embedding_function=embedding_function
        )
        logger.debug(f"Retrieved existing collection: {name}")
        return collection
    
    except Exception:
        # Collection doesn't exist, create it
        try:
            collection = client.create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=embedding_function
            )
            logger.info(f"Created new collection: {name}")
            return collection
        
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            return None


def safe_add_documents(
    collection: Any,
    documents: List[str],
    ids: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """
    Safely add documents to collection with error handling.
    
    Args:
        collection: ChromaDB collection
        documents: List of document texts
        ids: List of document IDs
        metadatas: Optional list of metadata dicts
    
    Returns:
        True if successful, False otherwise
    """
    if not collection:
        logger.error("Collection is None")
        return False
    
    if len(documents) != len(ids):
        logger.error("Documents and IDs length mismatch")
        return False
    
    try:
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        logger.debug(f"Added {len(documents)} documents to collection")
        return True
    
    except Exception as e:
        logger.error(f"Failed to add documents: {e}")
        return False


def safe_query_collection(
    collection: Any,
    query_texts: List[str],
    n_results: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Safely query collection with error handling.
    
    Args:
        collection: ChromaDB collection
        query_texts: List of query strings
        n_results: Number of results to return
    
    Returns:
        Query results or None on error
    """
    if not collection:
        logger.error("Collection is None")
        return None
    
    try:
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        return results
    
    except Exception as e:
        logger.error(f"Failed to query collection: {e}")
        return None


def safe_delete_collection(client: Any, name: str) -> bool:
    """
    Safely delete a collection.
    
    Args:
        client: ChromaDB client
        name: Collection name
    
    Returns:
        True if successful, False otherwise
    """
    if not client:
        logger.error("ChromaDB client is None")
        return False
    
    try:
        client.delete_collection(name=name)
        logger.info(f"Deleted collection: {name}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete collection {name}: {e}")
        return False


def reset_chroma_database(client: Any) -> bool:
    """
    Reset entire ChromaDB database (USE WITH CAUTION!).
    
    Args:
        client: ChromaDB client
    
    Returns:
        True if successful, False otherwise
    """
    if not client:
        logger.error("ChromaDB client is None")
        return False
    
    try:
        client.reset()
        logger.warning("ChromaDB database has been reset!")
        return True
    
    except Exception as e:
        logger.error(f"Failed to reset ChromaDB: {e}")
        return False
