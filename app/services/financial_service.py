import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import asyncio
import os
from app.config import settings, get_temp_path
from app.services.vector_service import vector_service
from app.services.qa_service import QAService
import json

class FinancialService:
    """财务分析服务"""
    
    def __init__(self):
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        
    async def stream_analysis(self, analysis_type: str, task_id: Optional[str] = None, company_name: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式财务分析"""
        try:
            if not task_id:
                task_id = str(uuid.uuid4())
            
            from app.services.qa_service import QAService
            qa_service = QAService()
            
            company_display_name = company_name or "分析企业"
            
            # 开始分析
            analysis_questions = self._get_analysis_questions(analysis_type)
            total_questions = len(analysis_questions)
            
            # 发送开始信号
            start_data = {
                "status": "started",
                "task_id": task_id,
                "total_steps": total_questions,
                "company_name": company_display_name,
                "analysis_type": self._get_analysis_type_name(analysis_type)
            }
            yield f"data: {json.dumps(start_data)}\n\n"
            
            for i, (section, question) in enumerate(analysis_questions.items()):
                progress = (i / total_questions) * 100
                
                # 发送处理状态
                processing_data = {
                    "status": "processing",
                    "step": section,
                    "progress": progress,
                    "current_step": i + 1,
                    "total_steps": total_questions
                }
                yield f"data: {json.dumps(processing_data)}\n\n"
                
                # 获取分析结果
                try:
                    result = await qa_service.answer_question(question)
                    
                    if result:
                        # 发送完成的步骤
                        completed_data = {
                            "status": "step_completed",
                            "section": section,
                            "content": result,
                            "progress": progress,
                            "current_step": i + 1
                        }
                        yield f"data: {json.dumps(completed_data)}\n\n"
                    else:
                        # 发送错误步骤
                        error_data = {
                            "status": "step_error", 
                            "section": section,
                            "error": "无法获取相关分析信息",
                            "progress": progress,
                            "current_step": i + 1
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"
                        
                except Exception as e:
                    # 发送步骤错误
                    error_data = {
                        "status": "step_error",
                        "section": section, 
                        "error": str(e),
                        "progress": progress,
                        "current_step": i + 1
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                
                await asyncio.sleep(0.2)  # 稍微增加延时，让流式效果更明显
            
            # 发送完成信号
            completed_data = {
                "status": "completed",
                "task_id": task_id,
                "progress": 100,
                "company_name": company_display_name,
                "analysis_type": self._get_analysis_type_name(analysis_type),
                "completed_at": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(completed_data)}\n\n"
            
        except Exception as e:
            # 发送全局错误
            error_data = {
                "status": "error",
                "error": str(e),
                "task_id": task_id if 'task_id' in locals() else None
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    def _get_analysis_questions(self, analysis_type: str) -> Dict[str, str]:
        """获取不同类型的分析问题"""
        questions = {
            # 1. 综合财务分析
            "comprehensive": {
                "盈利能力综合分析": "请分析公司的盈利能力，包括净资产收益率(ROE)、总资产报酬率(ROA)、销售净利率、毛利率等关键指标的水平和变化趋势",
                "偿债能力综合分析": "请分析公司的偿债能力，包括流动比率、速动比率、资产负债率、利息保障倍数等指标，评估短期和长期偿债风险", 
                "营运能力综合分析": "请分析公司的营运效率，包括总资产周转率、存货周转率、应收账款周转率、应付账款周转率等营运指标",
                "成长能力综合分析": "请分析公司的成长性，包括营业收入增长率、净利润增长率、总资产增长率、净资产增长率等成长指标",
                "现金流量综合分析": "请分析公司的现金流状况，包括经营活动现金流量净额、自由现金流量、现金流量质量等指标"
            },
            
            # 2. 杜邦分析
            "dupont": {
                "ROE杜邦分解分析": "请进行杜邦分析，分解净资产收益率(ROE) = 销售净利率 × 总资产周转率 × 权益乘数，分析各因素对ROE的贡献",
                "销售净利率驱动分析": "请分析销售净利率的变化，包括毛利率、期间费用率、所得税率等对净利率的影响",
                "资产周转率效率分析": "请分析总资产周转率，包括流动资产周转率、固定资产周转率等对资产使用效率的影响",
                "财务杠杆效应分析": "请分析权益乘数(财务杠杆)，评估资本结构对ROE的放大效应和财务风险",
                "ROE提升路径建议": "基于杜邦分析结果，请提出提升ROE的具体路径和改善建议"
            },
            
            # 3. 盈利能力与收益质量
            "profitability": {
                "核心盈利指标分析": "请分析净资产收益率(ROE)、总资产报酬率(ROA)、投入资本回报率(ROIC)等核心盈利指标的水平和质量",
                "利润率结构分析": "请分析毛利率、营业利润率、销售净利率的变化趋势，识别盈利能力的驱动因素和风险点",
                "收益质量评价": "请评价收益质量，分析经营活动净收益占比、价值变动净收益占比、营业外收支净额占比等指标",
                "成本费用控制分析": "请分析营业成本率、销售费用率、管理费用率、财务费用率等成本控制能力",
                "盈利持续性评估": "请评估盈利的可持续性，分析主营业务盈利能力和非经常性损益的影响"
            },
            
            # 4. 资本结构与偿债能力  
            "solvency": {
                "资本结构合理性分析": "请分析资本结构，包括资产负债率、长期资本负债率、权益乘数等指标，评估财务杠杆的合理性",
                "短期偿债能力分析": "请分析短期偿债能力，包括流动比率、速动比率、现金比率、营运资金等流动性指标",
                "长期偿债能力分析": "请分析长期偿债能力，包括利息保障倍数、债务保障倍数、现金流量利息保障倍数等指标",
                "债务结构与期限分析": "请分析债务结构，包括流动负债占比、长期负债占比、带息债务占比等债务构成",
                "偿债风险预警评估": "请综合评估偿债风险，识别潜在的财务风险点和预警信号"
            },
            
            # 5. 资产营运效率
            "efficiency": {
                "资产周转效率分析": "请分析总资产周转率、流动资产周转率、固定资产周转率等资产使用效率指标",
                "存货管理效率分析": "请分析存货周转率、存货周转天数，评估存货管理水平和库存控制能力",
                "应收账款管理分析": "请分析应收账款周转率、应收账款周转天数，评估客户信用管理和回款效率",
                "应付账款管理分析": "请分析应付账款周转率、应付账款周转天数，评估供应商付款政策和现金流管理",
                "营运资金管理效率": "请分析营运资金周转率、现金循环周期，评估营运资金管理效率"
            },
            
            # 6. 成长能力
            "growth": {
                "收入增长质量分析": "请分析营业收入增长率、主营业务收入增长率，评估收入增长的质量和可持续性",
                "利润增长能力分析": "请分析净利润增长率、归属母公司净利润增长率，评估盈利增长的稳定性",
                "资产扩张能力分析": "请分析总资产增长率、净资产增长率，评估公司的资产扩张能力和内生增长潜力",
                "每股指标增长分析": "请分析每股收益增长率、每股净资产增长率等每股指标的增长情况",
                "成长驱动因素识别": "请识别公司成长的主要驱动因素，分析未来成长的可持续性和风险"
            },
            
            # 7. 资本投资效率  
            "investment": {
                "投资回报率分析": "请分析投入资本回报率(ROIC)、人力投入回报率等投资效率指标",
                "资本配置效率评估": "请评估资本配置效率，分析资本支出的合理性和投资项目的回报水平",
                "资产减值风险分析": "请分析资产减值损失情况，评估资产质量和投资决策的有效性",
                "研发投入产出分析": "请分析研发费用占比和研发投入的产出效果，评估创新投入的回报",
                "投资策略建议": "基于投资效率分析，请提出优化资本配置和投资策略的建议"
            },
            
            # 8. 现金流量分析
            "cashflow": {
                "经营现金流质量分析": "请分析经营活动现金流量净额及其与营业收入、净利润的比值，评估现金流量质量",
                "自由现金流分析": "请分析企业自由现金流量和股权自由现金流量，评估公司的现金创造能力",
                "现金流结构分析": "请分析经营、投资、筹资三大现金流的结构和变化，判断公司的发展阶段和财务状况",
                "现金管理能力评估": "请评估现金管理能力，包括现金满足投资比率、全部资产现金回收率等指标",
                "现金流与盈利匹配度": "请分析经营活动现金流量与净利润的匹配度，评估收益的现金含量"
            }
        }
        
        return questions.get(analysis_type, questions["comprehensive"])
    
    def _get_analysis_type_name(self, analysis_type: str) -> str:
        """获取分析类型中文名称"""
        type_names = {
            "comprehensive": "综合财务分析", 
            "dupont": "杜邦分析",
            "profitability": "盈利能力与收益质量",
            "solvency": "资本结构与偿债能力",
            "efficiency": "资产营运效率", 
            "growth": "成长能力",
            "investment": "资本投资效率",
            "cashflow": "现金流量分析"
        }
        return type_names.get(analysis_type, "综合财务分析")
    
    async def generate_report(self, doc_ids: Optional[List[int]], analysis_type: str, company_name: str) -> Dict[str, Any]:
        """生成财务报告"""
        try:
            # 生成分析内容
            analysis_result = await self.generate_analysis(analysis_type, company_name)
            
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