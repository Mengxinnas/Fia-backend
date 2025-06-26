import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
import jieba
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

class VectorService:
    """向量化服务"""
    
    def __init__(self):
        self.vector_dimension = 768
        self.chunk_size = 1000
        self.min_chunk_length = 50
        
        self.index = faiss.IndexFlatL2(self.vector_dimension)
        self.document_store: Dict[int, Dict[str, Any]] = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.vector_dimension,
            stop_words=None,
            ngram_range=(1, 2)
        )
        self.tfidf_fitted = False
        self.doc_id_counter = 0
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 保留中文、英文、数字和基本符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,\-()（）\[\]【】{}""''：:;；!！?？]', '', text)
        return text.strip()
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """文本转向量"""
        # 预处理文本
        processed_text = self._preprocess_text(text)
        
        # 中文分词
        words = list(jieba.cut(processed_text))
        
        # 数字特殊处理
        processed_words = []
        for word in words:
            if re.match(r'^[\d.,\-]+$', word):
                processed_words.append(f"NUM_{word}")
            else:
                processed_words.append(word)
        
        final_text = ' '.join(processed_words)
        
        # 如果TF-IDF未训练，使用当前文本训练
        if not self.tfidf_fitted:
            self.tfidf_vectorizer.fit([final_text])
            self.tfidf_fitted = True
        
        # 向量化
        try:
            vector = self.tfidf_vectorizer.transform([final_text]).toarray().flatten()
        except:
            # 如果转换失败，重新训练
            self.tfidf_vectorizer.fit([final_text])
            self.tfidf_fitted = True
            vector = self.tfidf_vectorizer.transform([final_text]).toarray().flatten()
        
        # 确保向量维度正确
        if len(vector) < self.vector_dimension:
            padded_vector = np.zeros(self.vector_dimension)
            padded_vector[:len(vector)] = vector
            return padded_vector.astype('float32')
        else:
            return vector[:self.vector_dimension].astype('float32')
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """将文本分割成块"""
        sentences = re.split(r'[。！？\n]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果当前块加上新句子后超过限制，保存当前块
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + "。"
        
        # 添加最后一块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # 过滤太短的块
        chunks = [chunk for chunk in chunks if len(chunk) >= self.min_chunk_length]
        
        return chunks
    
    async def add_document(self, text: str, filename: str) -> str:
        """添加文档到向量数据库"""
        try:
            # 分割文本
            chunks = self._split_text_into_chunks(text)
            
            if not chunks:
                raise ValueError("文档分块后为空")
            
            # 为每个块生成向量
            vectors = []
            chunk_info = []
            
            for i, chunk in enumerate(chunks):
                try:
                    vector = self._text_to_vector(chunk)
                    vectors.append(vector)
                    
                    chunk_info.append({
                        'text': chunk,
                        'chunk_id': i,
                        'length': len(chunk)
                    })
                except Exception as e:
                    print(f"处理块 {i} 时出错: {e}")
                    continue
            
            if not vectors:
                raise ValueError("无法生成有效向量")
            
            # 添加到FAISS索引
            vectors_array = np.array(vectors).astype('float32')
            start_idx = self.index.ntotal
            self.index.add(vectors_array)
            
            # 存储文档信息
            doc_id = self.doc_id_counter
            self.doc_id_counter += 1
            
            self.document_store[doc_id] = {
                'filename': filename,
                'text': text,
                'chunks': chunk_info,
                'vector_indices': list(range(start_idx, start_idx + len(vectors))),
                'created_at': datetime.now().isoformat(),
                'chunk_count': len(chunks),
                'text_length': len(text)
            }
            
            return str(doc_id)
            
        except Exception as e:
            print(f"添加文档时出错: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            if self.index.ntotal == 0:
                return []
            
            # 将查询转换为向量
            query_vector = self._text_to_vector(query)
            query_vector = query_vector.reshape(1, -1).astype('float32')
            
            # 搜索
            actual_k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_vector, actual_k)
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS返回-1表示无效索引
                    continue
                
                # 找到对应的文档和块
                chunk_info = self._find_chunk_by_vector_index(idx)
                if chunk_info:
                    results.append({
                        'text': chunk_info['text'],
                        'filename': chunk_info['filename'],
                        'score': float(distance),
                        'chunk_id': chunk_info['chunk_id'],
                        'doc_id': chunk_info['doc_id']
                    })
            
            return results
            
        except Exception as e:
            print(f"搜索时出错: {e}")
            return []
    
    def _find_chunk_by_vector_index(self, vector_idx: int) -> Optional[Dict[str, Any]]:
        """根据向量索引找到对应的文档块"""
        for doc_id, doc_info in self.document_store.items():
            if vector_idx in doc_info['vector_indices']:
                # 找到在该文档中的位置
                local_idx = doc_info['vector_indices'].index(vector_idx)
                chunk = doc_info['chunks'][local_idx]
                
                return {
                    'text': chunk['text'],
                    'filename': doc_info['filename'],
                    'chunk_id': chunk['chunk_id'],
                    'doc_id': doc_id
                }
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_docs = len(self.document_store)
        total_vectors = self.index.ntotal
        total_text_length = sum(doc['text_length'] for doc in self.document_store.values())
        
        return {
            'total_documents': total_docs,
            'total_vectors': total_vectors,
            'total_text_length': total_text_length,
            'average_chunks_per_doc': total_vectors / total_docs if total_docs > 0 else 0
        }

# 创建全局实例
vector_service = VectorService() 