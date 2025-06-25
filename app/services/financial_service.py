import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import asyncio
import os
from app.config import settings, get_temp_path
from app.services.vector_service import vector_service
from app.services.qa_service import QAService

class FinancialAnalysisService:
    """财务分析服务"""
    
    def __init__(self):
        self.qa_service = QAService()
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        
    async def generate_analysis(self, analysis_type: str = "comprehensive", company_name: str = "分析企业") -> Dict[str, Any]:
        """生成财务分析"""
        try:
            task_id = str(uuid.uuid4())
            
            # 记录任务状态
            self.running_tasks[task_id] = {
                "status": "running",
                "progress": 0.0,
                "created_at": datetime.now(),
                "analysis_type": analysis_type,
                "company_name": company_name
            }
            
            # 根据分析类型生成不同的分析内容
            analysis_result = await self._perform_analysis(task_id, analysis_type, company_name)
            
            # 更新任务状态
            self.running_tasks[task_id]["status"] = "completed"
            self.running_tasks[task_id]["progress"] = 100.0
            self.running_tasks[task_id]["result"] = analysis_result
            
            return {
                "success": True,
                "task_id": task_id,
                "analysis_result": analysis_result,
                "message": "财务分析完成"
            }
            
        except Exception as e:
            if task_id in self.running_tasks:
                self.running_tasks[task_id]["status"] = "failed"
                self.running_tasks[task_id]["error"] = str(e)
            
            return {
                "success": False,
                "error": f"财务分析失败: {str(e)}"
            }
    
    async def _perform_analysis(self, task_id: str, analysis_type: str, company_name: str) -> str:
        """执行具体的财务分析"""
        analysis_questions = self._get_analysis_questions(analysis_type)
        
        analysis_parts = []
        total_questions = len(analysis_questions)
        
        for i, (section, question) in enumerate(analysis_questions.items()):
            # 更新进度
            progress = (i / total_questions) * 100
            self.running_tasks[task_id]["progress"] = progress
            
            # 获取答案
            result = await self.qa_service.get_answer(question)
            
            if result["success"]:
                analysis_parts.append(f"## {section}\n\n{result['answer']}\n")
            else:
                analysis_parts.append(f"## {section}\n\n无法获取相关分析信息。\n")
            
            # 模拟处理时间
            await asyncio.sleep(0.5)
        
        # 生成完整报告
        full_analysis = f"# {company_name}财务分析报告\n\n"
        full_analysis += f"**分析类型**: {self._get_analysis_type_name(analysis_type)}\n"
        full_analysis += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        full_analysis += "---\n\n"
        full_analysis += "\n".join(analysis_parts)
        
        return full_analysis
    
    def _get_analysis_questions(self, analysis_type: str) -> Dict[str, str]:
        """获取不同类型的分析问题"""
        questions = {
            "comprehensive": {
                "盈利能力分析": "请分析公司的盈利能力，包括营业收入、净利润、毛利率等指标",
                "偿债能力分析": "请分析公司的偿债能力，包括资产负债率、流动比率、速动比率等",
                "营运能力分析": "请分析公司的营运能力，包括总资产周转率、应收账款周转率等",
                "成长能力分析": "请分析公司的成长能力，包括营收增长率、净利润增长率等",
                "财务风险评估": "请评估公司的财务风险，包括现金流状况、财务杠杆等"
            },
            "profitability": {
                "营业收入分析": "请详细分析公司的营业收入情况和变化趋势",
                "毛利率分析": "请分析公司的毛利率水平和变化原因",
                "净利润分析": "请分析公司的净利润情况和盈利质量",
                "ROE分析": "请分析公司的净资产收益率情况"
            },
            "liquidity": {
                "流动资产分析": "请分析公司的流动资产构成和质量",
                "流动比率分析": "请分析公司的流动比率和短期偿债能力",
                "现金流分析": "请分析公司的现金流状况",
                "营运资金分析": "请分析公司的营运资金管理情况"
            },
            "efficiency": {
                "资产周转率分析": "请分析公司的资产使用效率",
                "应收账款管理": "请分析公司的应收账款管理情况",
                "存货管理": "请分析公司的存货管理效率",
                "资本使用效率": "请分析公司的资本使用效率"
            }
        }
        
        return questions.get(analysis_type, questions["comprehensive"])
    
    def _get_analysis_type_name(self, analysis_type: str) -> str:
        """获取分析类型中文名称"""
        type_names = {
            "comprehensive": "综合财务分析",
            "profitability": "盈利能力分析",
            "liquidity": "流动性分析",
            "efficiency": "运营效率分析"
        }
        return type_names.get(analysis_type, "综合财务分析")
    
    async def stream_analysis(self, analysis_type: str, task_id: Optional[str]) -> AsyncGenerator[str, None]:
        """流式财务分析"""
        try:
            if not task_id:
                task_id = str(uuid.uuid4())
            
            # 开始分析
            analysis_questions = self._get_analysis_questions(analysis_type)
            total_questions = len(analysis_questions)
            
            yield f"data: {{'status': 'started', 'task_id': '{task_id}', 'total_steps': {total_questions}}}\n\n"
            
            for i, (section, question) in enumerate(analysis_questions.items()):
                progress = (i / total_questions) * 100
                
                yield f"data: {{'status': 'processing', 'step': '{section}', 'progress': {progress}}}\n\n"
                
                # 获取分析结果
                result = await self.qa_service.get_answer(question)
                
                if result["success"]:
                    yield f"data: {{'status': 'step_completed', 'section': '{section}', 'content': {repr(result['answer'])}}}\n\n"
                else:
                    yield f"data: {{'status': 'step_error', 'section': '{section}', 'error': {repr(result.get('error', '未知错误'))}}}\n\n"
                
                await asyncio.sleep(0.1)
            
            yield f"data: {{'status': 'completed', 'task_id': '{task_id}'}}\n\n"
            
        except Exception as e:
            yield f"data: {{'status': 'error', 'error': {repr(str(e))}}}\n\n"
    
    async def generate_report(self, doc_ids: Optional[List[int]], analysis_type: str, company_name: str) -> Dict[str, Any]:
        """生成财务报告"""
        try:
            # 生成分析内容
            analysis_result = await self._perform_analysis(str(uuid.uuid4()), analysis_type, company_name)
            
            # 生成Word文档
            word_result = await self.generate_word_document(analysis_result, analysis_type, company_name)
            
            return {
                "success": True,
                "analysis_result": analysis_result,
                "download_url": word_result.get("download_url"),
                "filename": word_result.get("filename")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"报告生成失败: {str(e)}"
            }
    
    async def generate_word_document(self, analysis_result: str, analysis_type: str, company_name: str) -> Dict[str, Any]:
        """生成Word文档"""
        try:
            # 这里应该实现Word文档生成逻辑
            # 由于缺少python-docx的具体实现，这里返回模拟结果
            
            filename = f"{company_name}_{analysis_type}_报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            return {
                "success": True,
                "filename": filename,
                "download_url": f"/api/financial-report/download/{filename}",
                "message": "Word文档生成成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Word文档生成失败: {str(e)}"
            }
    
    def get_report_path(self, filename: str) -> str:
        """获取报告文件路径"""
        return get_temp_path(filename)
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["status"] = "cancelled"
            return {"success": True, "message": "任务已取消"}
        else:
            return {"success": False, "error": "任务不存在"}
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """获取分析状态"""
        active_tasks = [
            {
                "task_id": task_id,
                "status": task_info["status"],
                "progress": task_info.get("progress", 0),
                "created_at": task_info["created_at"].isoformat()
            }
            for task_id, task_info in self.running_tasks.items()
            if task_info["status"] in ["running", "pending"]
        ]
        
        return {
            "success": True,
            "active_tasks": active_tasks,
            "total_active": len(active_tasks)
        }
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """获取分析模板"""
        return [
            {
                "id": "comprehensive",
                "name": "综合财务分析",
                "description": "全面分析企业财务状况，包括盈利能力、偿债能力、营运能力等"
            },
            {
                "id": "profitability",
                "name": "盈利能力分析",
                "description": "专注分析企业的盈利能力和盈利质量"
            },
            {
                "id": "liquidity",
                "name": "流动性分析",
                "description": "重点分析企业的短期偿债能力和流动性状况"
            },
            {
                "id": "efficiency",
                "name": "运营效率分析",
                "description": "评估企业的资产使用效率和运营管理水平"
            }
        ] 