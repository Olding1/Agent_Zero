"""
Agent Zero 项目清理脚本

自动化执行文档和脚本的整理工作:
- 归档历史文档到 docs/archive/
- 移动工具脚本到 scripts/fixes/
- 删除临时/冗余文档
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class ProjectCleanup:
    def __init__(self, project_root: str, dry_run: bool = True):
        self.root = Path(project_root)
        self.dry_run = dry_run
        self.backup_dir = self.root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        print(f"{emoji.get(level, 'ℹ️')} {message}")
    
    def create_backup(self):
        """创建备份"""
        if self.dry_run:
            self.log("DRY RUN: 将创建备份目录", "INFO")
            return
        
        self.backup_dir.mkdir(exist_ok=True)
        self.log(f"创建备份目录: {self.backup_dir}", "SUCCESS")
    
    def create_directories(self):
        """创建归档和脚本目录"""
        dirs = [
            "docs/archive/phase1",
            "docs/archive/phase2",
            "docs/archive/phase3",
            "docs/archive/phase4",
            "docs/archive/debugging",
            "scripts/fixes"
        ]
        
        for d in dirs:
            target = self.root / d
            if self.dry_run:
                self.log(f"DRY RUN: 将创建目录 {d}", "INFO")
            else:
                target.mkdir(parents=True, exist_ok=True)
                self.log(f"创建目录: {d}", "SUCCESS")
    
    def move_file(self, source: str, dest: str, description: str = ""):
        """移动文件"""
        src = self.root / source
        dst = self.root / dest
        
        if not src.exists():
            self.log(f"文件不存在,跳过: {source}", "WARNING")
            return False
        
        if self.dry_run:
            self.log(f"DRY RUN: {source} → {dest} {description}", "INFO")
            return True
        
        # 确保目标目录存在
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # 备份
        if not self.dry_run and self.backup_dir.exists():
            backup_file = self.backup_dir / source
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, backup_file)
        
        # 移动
        shutil.move(str(src), str(dst))
        self.log(f"移动: {source} → {dest} {description}", "SUCCESS")
        return True
    
    def delete_file(self, filepath: str, reason: str = ""):
        """删除文件"""
        target = self.root / filepath
        
        if not target.exists():
            self.log(f"文件不存在,跳过: {filepath}", "WARNING")
            return False
        
        if self.dry_run:
            self.log(f"DRY RUN: 将删除 {filepath} ({reason})", "INFO")
            return True
        
        # 备份
        if self.backup_dir.exists():
            backup_file = self.backup_dir / filepath
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_file)
        
        # 删除
        target.unlink()
        self.log(f"删除: {filepath} ({reason})", "SUCCESS")
        return True
    
    def archive_phase_docs(self):
        """归档 Phase 文档"""
        self.log("\n📦 归档历史文档...", "INFO")
        
        archives = {
            # Phase 1
            "phase1_summary.md": "docs/archive/phase1/phase1_summary.md",
            
            # Phase 2
            "phase2_summary.md": "docs/archive/phase2/phase2_summary.md",
            "RAG_Implementation_Plan.md": "docs/archive/phase2/RAG_Implementation_Plan.md",
            
            # Phase 3
            "phase3_summary.md": "docs/archive/phase3/phase3_summary.md",
            "phase3_progress.md": "docs/archive/phase3/phase3_progress.md",
            "phase3_integration_test_results.md": "docs/archive/phase3/phase3_integration_test_results.md",
            "phase3_issues_explained.md": "docs/archive/phase3/phase3_issues_explained.md",
            "phase3_test_results_analysis.md": "docs/archive/phase3/phase3_test_results_analysis.md",
            "PM_Graph_Designer_改进实施计划.md": "docs/archive/phase3/PM_Graph_Designer_改进实施计划.md",
            "Phase3_修改实施计划.md": "docs/archive/phase3/Phase3_修改实施计划.md",
            "router_pattern_evaluation.md": "docs/archive/phase3/router_pattern_evaluation.md",
            
            # Phase 4
            "phase4_summary.md": "docs/archive/phase4/phase4_summary.md",
            "phase4_task_4_1_summary.md": "docs/archive/phase4/phase4_task_4_1_summary.md",
            "phase4_tasks_4_4_to_4_6_summary.md": "docs/archive/phase4/phase4_tasks_4_4_to_4_6_summary.md",
            "phase4_deepeval_optimized.md": "docs/archive/phase4/phase4_deepeval_optimized.md",
            
            # Debugging
            "COMPLETE_DEBUGGING_SUMMARY.md": "docs/archive/debugging/COMPLETE_DEBUGGING_SUMMARY.md",
        }
        
        for src, dst in archives.items():
            self.move_file(src, dst, "(归档)")
    
    def delete_redundant_docs(self):
        """删除冗余文档"""
        self.log("\n🗑️ 删除冗余/临时文档...", "INFO")
        
        to_delete = {
            # 冗余计划
            "AgentFactory_实施计划.md": "已整合到详细计划",
            "PM_Graph_Designer_Improved_Plan.md": "有中文版",
            "Phase6_Runtime_Evolution_详细实施计划.md": "已有 Phase6_final_summary",
            "phase6_completion_plan.md": "已有 Phase6_final_summary",
            "PHASE6_IMPLEMENTATION_STATUS.md": "已有最终总结",
            
            # 临时调试文档
            "AGENT_TEMPLATE_FIXES.md": "临时修复记录",
            "RAG_TEST_FAILURE_ANALYSIS.md": "问题已解决",
            "TEST_DIAGNOSTIC.md": "临时诊断",
            "PHASE6_DEBUGGING_SUMMARY.md": "已有最终总结",
            "test_generator_fix_summary.md": "临时修复",
        }
        
        for filepath, reason in to_delete.items():
            self.delete_file(filepath, reason)
    
    def move_scripts(self):
        """移动工具脚本"""
        self.log("\n🔧 移动工具脚本...", "INFO")
        
        scripts = {
            "fix_collection_name.py": "scripts/fixes/fix_collection_name.py",
            "fix_embedding_config.py": "scripts/fixes/fix_embedding_config.py",
            "fix_pydantic_warnings.py": "scripts/fixes/fix_pydantic_warnings.py",
            "update_agent_judge_config.py": "scripts/fixes/update_agent_judge_config.py",
        }
        
        for src, dst in scripts.items():
            self.move_file(src, dst, "(工具脚本)")
    
    def delete_temp_scripts(self):
        """删除临时测试脚本"""
        self.log("\n🧪 删除临时测试脚本...", "INFO")
        
        to_delete = {
            "test_debug_output.py": "临时测试",
            "test_rag_routing.py": "临时测试",
            # test_phase6_e2e.py 可选
            # "test_phase6_e2e.py": "临时 E2E 测试",
        }
        
        for filepath, reason in to_delete.items():
            self.delete_file(filepath, reason)
    
    def create_readme_update(self):
        """创建 README 更新建议"""
        self.log("\n📝 README 更新建议...", "INFO")
        
        readme_addition = """
## 📚 文档结构

- `README.md` - 项目概览
- `Agent_Zero_详细实施计划.md` - 完整实施计划
- `Agent Zero项目计划书.md` - 原始项目计划
- `Phase6_final_summary.md` - Phase 6 最终总结
- `PHASE6_TEST_GUIDE.md` - Phase 6 测试指南
- `docs/archive/` - 历史文档归档
  - `phase1/` - Phase 1 相关文档
  - `phase2/` - Phase 2 相关文档
  - `phase3/` - Phase 3 相关文档
  - `phase4/` - Phase 4 相关文档
  - `debugging/` - 调试总结文档
- `scripts/fixes/` - 修复工具脚本
"""
        
        if self.dry_run:
            self.log("DRY RUN: 将在 README.md 中添加文档结构说明", "INFO")
        else:
            self.log("请手动将以下内容添加到 README.md:", "INFO")
            print("\n" + "="*70)
            print(readme_addition)
            print("="*70 + "\n")
    
    def verify_cleanup(self):
        """验证清理结果"""
        self.log("\n✅ 验证清理结果...", "INFO")
        
        # 检查核心文档
        core_docs = [
            "README.md",
            "Agent_Zero_详细实施计划.md",
            "Agent Zero项目计划书.md",
            "Phase6_final_summary.md",
            "PHASE6_TEST_GUIDE.md"
        ]
        
        for doc in core_docs:
            if (self.root / doc).exists():
                self.log(f"核心文档存在: {doc}", "SUCCESS")
            else:
                self.log(f"核心文档缺失: {doc}", "ERROR")
        
        # 检查归档目录
        archive_dirs = [
            "docs/archive/phase1",
            "docs/archive/phase2",
            "docs/archive/phase3",
            "docs/archive/phase4",
            "docs/archive/debugging"
        ]
        
        for d in archive_dirs:
            if (self.root / d).exists():
                count = len(list((self.root / d).glob("*.md")))
                self.log(f"归档目录: {d} ({count} 个文件)", "SUCCESS")
            else:
                self.log(f"归档目录缺失: {d}", "WARNING")
        
        # 检查脚本目录
        if (self.root / "scripts/fixes").exists():
            count = len(list((self.root / "scripts/fixes").glob("*.py")))
            self.log(f"工具脚本目录: scripts/fixes/ ({count} 个文件)", "SUCCESS")
        else:
            self.log("工具脚本目录缺失: scripts/fixes/", "WARNING")
    
    def run(self):
        """执行清理"""
        self.log("="*70, "INFO")
        self.log("Agent Zero 项目清理", "INFO")
        self.log("="*70, "INFO")
        
        if self.dry_run:
            self.log("\n⚠️ DRY RUN 模式 - 不会实际修改文件", "WARNING")
        else:
            self.log("\n🚀 执行模式 - 将实际修改文件", "WARNING")
            self.create_backup()
        
        # 执行清理步骤
        self.create_directories()
        self.archive_phase_docs()
        self.delete_redundant_docs()
        self.move_scripts()
        self.delete_temp_scripts()
        self.create_readme_update()
        
        if not self.dry_run:
            self.verify_cleanup()
        
        self.log("\n" + "="*70, "INFO")
        if self.dry_run:
            self.log("DRY RUN 完成! 使用 --execute 参数执行实际清理", "SUCCESS")
        else:
            self.log(f"清理完成! 备份保存在: {self.backup_dir}", "SUCCESS")
        self.log("="*70, "INFO")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Zero 项目清理脚本")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="执行实际清理 (默认为 dry-run 模式)"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="项目根目录路径 (默认为当前目录)"
    )
    
    args = parser.parse_args()
    
    cleanup = ProjectCleanup(
        project_root=args.project_root,
        dry_run=not args.execute
    )
    
    cleanup.run()
