# mongo_test_tool.py
"""
MongoDB Test Tool for WatsonX Orchestrate Agent
Combines connection and operations in a single file for easy testing
"""

import os
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, PyMongoError
from dotenv import load_dotenv
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import json


# Helper class for MongoDB connection (embedded)
class MongoDBConnection:
    def __init__(self):
        load_dotenv()
        self.connection_string = os.getenv('MONGODB_URI')
        if not self.connection_string:
            raise ValueError("MONGODB_URI not found in environment variables")
        
        self.client = None
        self.database = None
        self.collection = None
    
    def connect(self, database_name="test_db", collection_name="documents"):
        """Connect to MongoDB Atlas and select database/collection"""
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            
            self.database = self.client[database_name]
            self.collection = self.database[collection_name]
            
            return True
        except (ConnectionFailure, ConfigurationError, Exception):
            return False
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def get_collection(self):
        """Get the current collection object"""
        if self.collection is None:
            raise ValueError("Not connected to MongoDB. Call connect() first.")
        return self.collection


# Helper functions for MongoDB operations
def _ensure_connection(db_connection, database_name, collection_name):
    """Ensure we have an active connection"""
    success = db_connection.connect(database_name, collection_name)
    if not success:
        raise ConnectionError("Failed to connect to MongoDB")
    return True


def _insert_document_helper(name, status="active", additional_data=None, 
                           database_name="test_db", collection_name="documents"):
    """Helper function to insert a document"""
    db_connection = MongoDBConnection()
    try:
        _ensure_connection(db_connection, database_name, collection_name)
        collection = db_connection.get_collection()
        
        # Create document with minimal schema
        document = {
            "name": name,
            "status": status,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Add any additional data
        if additional_data and isinstance(additional_data, dict):
            document.update(additional_data)
        
        # Insert document
        result = collection.insert_one(document)
        
        return {
            "success": True,
            "message": "Document inserted successfully",
            "document_id": str(result.inserted_id),
            "document": document
        }
    
    except PyMongoError as e:
        return {
            "success": False,
            "message": f"MongoDB error: {str(e)}",
            "document_id": None,
            "document": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "document_id": None,
            "document": None
        }
    finally:
        db_connection.close_connection()


def _find_documents_helper(filter_dict=None, limit=10, include_schema=False,
                          database_name="test_db", collection_name="documents"):
    """Helper function to find documents"""
    db_connection = MongoDBConnection()
    try:
        _ensure_connection(db_connection, database_name, collection_name)
        collection = db_connection.get_collection()
        
        # Use empty filter if none provided
        if filter_dict is None:
            filter_dict = {}
        
        # Exclude schema documents by default unless specifically requested
        if not include_schema and "_schema" not in filter_dict:
            filter_dict["_schema"] = {"$exists": False}
        
        # Find documents
        cursor = collection.find(filter_dict).limit(limit)
        documents = []
        
        for doc in cursor:
            try:
                # Convert ObjectId to string for JSON serialization
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                
                # Convert datetime to string safely
                if 'created_at' in doc and doc['created_at']:
                    if hasattr(doc['created_at'], 'isoformat'):
                        doc['created_at'] = doc['created_at'].isoformat()
                
                # Convert updated_at if exists
                if 'updated_at' in doc and doc['updated_at']:
                    if hasattr(doc['updated_at'], 'isoformat'):
                        doc['updated_at'] = doc['updated_at'].isoformat()
                
                documents.append(doc)
                
            except Exception:
                continue
        
        return {
            "success": True,
            "message": f"Found {len(documents)} documents",
            "count": len(documents),
            "documents": documents
        }
    
    except PyMongoError as e:
        return {
            "success": False,
            "message": f"MongoDB error: {str(e)}",
            "count": 0,
            "documents": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "count": 0,
            "documents": []
        }
    finally:
        db_connection.close_connection()


def _test_connection_helper(database_name="test_db"):
    """Helper function to test MongoDB connection"""
    db_connection = MongoDBConnection()
    try:
        success = db_connection.connect(database_name, "test_collection")
        if success:
            # Get basic database stats
            db = db_connection.database
            stats = db.command("dbstats")
            collections = db.list_collection_names()
            
            return {
                "success": True,
                "message": "Successfully connected to MongoDB",
                "database": database_name,
                "collections_count": len(collections),
                "collections": collections[:5],  # Show first 5 collections
                "database_size": f"{stats.get('storageSize', 0) / 1024:.2f} KB"
            }
        else:
            return {
                "success": False,
                "message": "Failed to connect to MongoDB",
                "database": database_name
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "database": database_name
        }
    finally:
        db_connection.close_connection()


# WatsonX Orchestrate Tools
@tool()
def mongodb_insert_test(document_name: str, status: str = "active") -> str:
    """Insert a test document into MongoDB.

    Args:
        document_name (str): Name of the document to insert
        status (str): Status of the document (default: "active")

    Returns:
        str: Result of the insert operation
    """
    
    try:
        # Add some test data
        additional_data = {
            "test_field": "This is a test document",
            "agent_created": True
        }
        
        result = _insert_document_helper(
            name=document_name,
            status=status,
            additional_data=additional_data
        )
        
        if result["success"]:
            return f"✅ Successfully inserted document '{document_name}' with ID: {result['document_id']}"
        else:
            return f"❌ Failed to insert document '{document_name}': {result['message']}"
            
    except Exception as e:
        return f"❌ Error inserting document: {str(e)}"


@tool()
def mongodb_search_documents(search_query: str = "all") -> str:
    """Search for documents in MongoDB.

    Args:
        search_query (str): Search criteria - "all" for all documents, or name to search by name

    Returns:
        str: List of found documents
    """
    
    try:
        # Prepare filter based on query
        if search_query.lower() == "all":
            filter_dict = {}
        else:
            filter_dict = {"name": {"$regex": search_query, "$options": "i"}}
        
        result = _find_documents_helper(filter_dict=filter_dict, limit=5, include_schema=False)
        
        if result["success"]:
            if result["count"] > 0:
                documents_info = []
                for doc in result["documents"]:
                    doc_info = f"• {doc.get('name', 'Unknown')} (Status: {doc.get('status', 'N/A')}, ID: {doc.get('_id', 'N/A')[:8]}...)"
                    documents_info.append(doc_info)
                
                return f"📄 Found {result['count']} documents:\n" + "\n".join(documents_info)
            else:
                return f"📭 No documents found matching '{search_query}'"
        else:
            return f"❌ Search failed: {result['message']}"
            
    except Exception as e:
        return f"❌ Error searching documents: {str(e)}"


@tool()
def mongodb_connection_test() -> str:
    """Test MongoDB connection and get database information.

    Returns:
        str: Connection status and database information
    """
    
    try:
        result = _test_connection_helper()
        
        if result["success"]:
            return (f"✅ MongoDB Connection Successful!\n"
                   f"📂 Database: {result['database']}\n"
                   f"📋 Collections: {result['collections_count']}\n"
                   f"💾 Database Size: {result['database_size']}\n"
                   f"📁 Sample Collections: {', '.join(result['collections']) if result['collections'] else 'None'}")
        else:
            return f"❌ MongoDB Connection Failed: {result['message']}"
            
    except Exception as e:
        return f"❌ Connection test error: {str(e)}"


@tool()
def mongodb_quick_demo() -> str:
    """Run a quick MongoDB demonstration by inserting a test document and retrieving it.

    Returns:
        str: Results of the demo operations
    """
    
    try:
        demo_name = f"demo_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Insert a demo document
        insert_result = _insert_document_helper(
            name=demo_name,
            status="demo",
            additional_data={
                "demo_type": "quick_test",
                "created_by": "watsonx_agent",
                "test_number": 1
            }
        )
        
        if not insert_result["success"]:
            return f"❌ Demo failed at insert: {insert_result['message']}"
        
        # Step 2: Retrieve the document
        find_result = _find_documents_helper(
            filter_dict={"name": demo_name},
            limit=1,
            include_schema=False
        )
        
        if not find_result["success"]:
            return f"❌ Demo failed at retrieval: {find_result['message']}"
        
        # Step 3: Format results
        if find_result["count"] > 0:
            doc = find_result["documents"][0]
            return (f"🎉 MongoDB Demo Successful!\n"
                   f"✅ Inserted: {demo_name}\n"
                   f"✅ Retrieved: Document ID {doc.get('_id', 'N/A')[:8]}...\n"
                   f"📊 Status: {doc.get('status', 'N/A')}\n"
                   f"⏰ Created: {doc.get('created_at', 'N/A')[:19]}")
        else:
            return "❌ Demo: Document inserted but not found during retrieval"
            
    except Exception as e:
        return f"❌ Demo error: {str(e)}"