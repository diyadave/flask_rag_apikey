import os
import faiss
import numpy as np
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, books_dir, faiss_db_dir):
        self.books_dir = Path(books_dir)
        self.faiss_db_dir = Path(faiss_db_dir)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunk_texts = []
        self.category_chunks = {}  # {category: [chunks]}
        self.faiss_index = None
        
        try:
            # Create directories if they don't exist
            self.faiss_db_dir.mkdir(parents=True, exist_ok=True)
            self.books_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Initializing PDFProcessor with books_dir: {self.books_dir}")
            logger.info(f"FAISS db will be stored in: {self.faiss_db_dir}")
            
            self._load_documents()
            self._create_faiss_index()
            
        except Exception as e:
            logger.error(f"Failed to initialize PDFProcessor: {str(e)}")
            raise

    def _load_documents(self):
        """Load and chunk PDF documents from category folders"""
        logger.info(f"Scanning for PDFs in: {self.books_dir}")
        
        pdf_count = 0
        for category_dir in self.books_dir.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                self.category_chunks[category_name] = []
                logger.info(f"Processing category: {category_name}")
                
                for pdf_file in category_dir.glob('*.pdf'):
                    try:
                        logger.info(f"  Reading PDF: {pdf_file.name}")
                        with fitz.open(pdf_file) as pdf:
                            text = "".join(page.get_text() for page in pdf)
                            if not text.strip():
                                logger.warning(f"  Empty PDF: {pdf_file.name}")
                                continue
                                
                            chunks = self._chunk_text(text)
                            self.chunk_texts.extend(chunks)
                            self.category_chunks[category_name].extend(chunks)
                            pdf_count += 1
                            
                    except Exception as e:
                        logger.error(f"  Failed to process {pdf_file.name}: {str(e)}")
                        continue

        if pdf_count == 0:
            logger.warning("No valid PDF files found in any category!")
        else:
            logger.info(f"Processed {pdf_count} PDFs with {len(self.chunk_texts)} chunks")

    def _chunk_text(self, text, chunk_size=500):
        """Split text into word-based chunks"""
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        logger.debug(f"Created {len(chunks)} chunks from text")
        return chunks

    def _create_faiss_index(self):
        """Create and save FAISS index from document chunks"""
        if not self.chunk_texts:
            logger.warning("No text chunks available for indexing")
            return
            
        logger.info("Creating FAISS index...")
        
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(self.chunk_texts)
            dim = embeddings.shape[1]
            
            # Create and populate index
            self.faiss_index = faiss.IndexFlatL2(dim)
            self.faiss_index.add(np.array(embeddings))
            
            # Save index and metadata
            faiss.write_index(self.faiss_index, str(self.faiss_db_dir / 'index.faiss'))
            
            with open(self.faiss_db_dir / 'chunks.pkl', 'wb') as f:
                pickle.dump({
                    'chunk_texts': self.chunk_texts,
                    'category_chunks': self.category_chunks,
                    'embedding_dim': dim
                }, f)
                
            logger.info(f"FAISS index created with {len(self.chunk_texts)} chunks")
            logger.info(f"Index saved to: {self.faiss_db_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {str(e)}")
            raise