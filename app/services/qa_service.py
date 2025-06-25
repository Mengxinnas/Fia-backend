import httpx
from typing import Dict, Any, List
from app.config import settings
from app.services.vector_service import vector_service

class QAService:
    """问答服务"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        
    async def get_answer(self, question: str) -> Dict[str, Any]:
        """获取问题答案"""
        try:
            # 1. 从向量数据库检索相关上下文
            context = await self._get_context(question)
            
            # 2. 调用AI生成答案
            answer = await self._generate_answer(question, context)
            
            # 3. 获取相关文档信息
            sources = await self._get_sources(question)
            
            return {
                "success": True,
                "answer": answer,
                "sources": sources,
                "context_used": len(context) > 0,
                "question": question
            }
            
        except Exception as e:
            print(f"问答处理错误: {str(e)}")
            return {
                "success": False,
                "answer": f"抱歉，处理您的问题时出现错误: {str(e)}",
                "sources": [],
                "context_used": False,
                "question": question
            }
    
    async def _get_context(self, question: str, max_length: int = 2000) -> str:
        """获取相关上下文"""
        try:
            results = vector_service.search(question, top_k=5)
            
            context_parts = []
            current_length = 0
            
            for result in results:
                text = result['text']
                if current_length + len(text) <= max_length:
                    context_parts.append(text)
                    current_length += len(text)
                else:
                    # 如果超出长度限制，截取部分文本
                    remaining = max_length - current_length
                    if remaining > 100:  # 至少保留100字符
                        context_parts.append(text[:remaining] + "...")
                    break
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"获取上下文错误: {str(e)}")
            return ""
    
    async def _generate_answer(self, question: str, context: str) -> str:
        """生成答案"""
        try:
            if not self.api_key:
                return "抱歉，AI服务未配置，无法生成答案。"
            
            # 构建系统提示词
            system_prompt = f"""你是一个专业的财务分析助手。请基于以下文档内容回答用户的问题。

文档内容：
{context}

请注意：
1. 只基于提供的文档内容回答问题
2. 如果文档中没有相关信息，请明确说明
3. 回答要准确、专业，并提供具体的数据支持
4. 使用中文回答"""

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json=payload
                )
                
                if response.status_code != 200:
                    raise Exception(f"AI服务调用失败: {response.status_code}")
                
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                return answer
                
        except Exception as e:
            print(f"生成答案错误: {str(e)}")
            if context:
                return f"基于文档内容，我找到了相关信息，但生成答案时出现错误: {str(e)}\n\n相关文档内容：\n{context[:500]}..."
            else:
                return f"抱歉，无法生成答案: {str(e)}"
    
    async def _get_sources(self, question: str) -> List[Dict[str, Any]]:
        """获取相关文档来源"""
        try:
            results = vector_service.search(question, top_k=3)
            
            sources = []
            for result in results:
                sources.append({
                    'filename': result.get('filename', ''),
                    'score': result.get('score', 0),
                    'text_preview': result['text'][:200] + '...' if len(result['text']) > 200 else result['text']
                })
            
            return sources
            
        except Exception as e:
            print(f"获取来源错误: {str(e)}")
            return [] 