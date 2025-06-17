import os
import faiss
import numpy as np
import logging
from config import Config
from langchain_groq import ChatGroq
from .pdf_processor import PDFProcessor 

logger = logging.getLogger(__name__)

class StoryGenerator:
    def __init__(self):
        try:
            self.groq_llm = ChatGroq(
            model_name=Config.GROQ_MODEL,
            temperature=0.7,
            max_tokens=2000,
            api_key=Config.GROQ_API_KEY,
            request_timeout=60  # was 30 or less, make it 60 or 90
        )

            
            self.pdf_processor = PDFProcessor(Config.BOOKS_DIR, Config.FAISS_DB_DIR)
            self.embedding_model = self.pdf_processor.embedding_model
            logger.info("✅ StoryGenerator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize StoryGenerator: {str(e)}")
            raise

    def get_relevant_chunks(self, query, category=None, k=5):
        try:
            query_embedding = self.embedding_model.encode(query)
            if category and category in self.pdf_processor.category_chunks:
                category_indices = [
                    i for i, chunk in enumerate(self.pdf_processor.chunk_texts)
                    if chunk in self.pdf_processor.category_chunks[category]
                ]
                if not category_indices:
                    return []

                category_embeddings = self.embedding_model.encode(
                    [self.pdf_processor.chunk_texts[i] for i in category_indices]
                )
                temp_index = faiss.IndexFlatL2(category_embeddings.shape[1])
                temp_index.add(np.array(category_embeddings))
                distances, indices = temp_index.search(np.array([query_embedding]), k)
                return [self.pdf_processor.chunk_texts[category_indices[i]] for i in indices[0] if i >= 0]
            else:
                distances, indices = self.pdf_processor.faiss_index.search(np.array([query_embedding]), k)
                return [self.pdf_processor.chunk_texts[i] for i in indices[0] if i >= 0]
        except Exception as e:
            logger.error(f"⚠ Error in get_relevant_chunks: {str(e)}")
            return []

    def generate_story(self, prompt, category=None):
        try:
            logger.info(f"📝 Generating story for: {prompt[:40]}...")
            context = ""
            if category:
                chunks = self.get_relevant_chunks(prompt, category, k=2)
                if chunks:
                    context = "\n\nRelevant context:\n" + "\n".join(chunks)

            prompt_template = f"""Write a concise story (under 300 words) about:
{prompt}{context}

Guidelines:
- Focus on key elements
- Use clear language
- Keep it engaging"""

            response = self.groq_llm.invoke(
                prompt_template,
                temperature=0.5,
                max_tokens=500
            )
            return {"response": response.content}
        except Exception as e:
            logger.error(f"⚠ Story generation failed: {str(e)}")
            return {"error": str(e)}
