#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词库自动学习模块 v1.4.0
功能：自动学习高频词汇、定期清理低价值词汇、自动扩展专业领域词汇
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from collections import Counter
from dataclasses import dataclass

# ============== 路径配置 ==============

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
VOCABULARY_DB_PATH = os.path.join(DATA_DIR, "vocabulary_db.json")
NEW_VOCABULARY_PATH = os.path.join(DATA_DIR, "new_vocabulary_found.json")
DETECTION_HISTORY_PATH = os.path.join(DATA_DIR, "detection_history.json")
VOCAB_FREQUENCY_PATH = os.path.join(DATA_DIR, "vocab_frequency.json")
AUTO_LEARN_CONFIG_PATH = os.path.join(DATA_DIR, "auto_learn_config.json")


# ============== 数据结构 ==============

@dataclass
class VocabFrequency:
    """词汇频率记录"""
    vocabulary: str
    count: int
    first_seen: str
    last_seen: str
    contexts: List[str]
    auto_added: bool = False


@dataclass
class AutoLearnConfig:
    """自动学习配置"""
    # 高频词汇自动加入阈值
    auto_add_threshold: int = 3  # 出现3次自动加入
    
    # 清理配置
    cleanup_days: int = 30  # 30天未出现的词汇清理
    min_frequency_to_keep: int = 2  # 至少出现2次才保留
    
    # 专业领域来源
    domain_sources: Dict[str, List[str]] = None
    
    # 最后更新时间
    last_auto_update: str = ""
    last_domain_expansion: str = ""
    
    def __post_init__(self):
        if self.domain_sources is None:
            self.domain_sources = {
                "科技": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "大模型", "AGI", "GPU", "算力", "芯片"],
                "生物制药": ["基因编辑", "CRISPR", "mRNA", "抗体", "疫苗", "临床试验", "新药", "靶向", "免疫疗法", "蛋白质"],
                "财经": ["IPO", "融资", "估值", "市盈率", "ROE", "ROI", "现金流", "资产负债", "分红", "回购"],
                "新能源": ["光伏", "储能", "锂电", "氢能", "碳中和", "ESG", "新能源车", "充电桩", "电池回收"],
            }


# ============== 词库管理类 ==============

class VocabAutoLearner:
    """词库自动学习器"""
    
    def __init__(self):
        self.vocab_db = self._load_json(VOCABULARY_DB_PATH, self._get_default_vocab_db())
        self.new_vocab = self._load_json(NEW_VOCABULARY_PATH, [])
        self.vocab_frequency = self._load_json(VOCAB_FREQUENCY_PATH, {})
        self.config = self._load_config()
        self.detection_history = self._load_json(DETECTION_HISTORY_PATH, [])
    
    def _load_json(self, path: str, default):
        """加载JSON文件"""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return default
    
    def _save_json(self, path: str, data):
        """保存JSON文件"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _get_default_vocab_db(self) -> Dict:
        """获取默认词汇库结构"""
        return {
            "scientific": {"极高风险": {}, "高风险": {}, "中风险": {}},
            "professional": {"科技": {}, "生物制药": {}, "财经": {}, "新能源": {}},
            "custom": {"极高风险": {}, "高风险": {}, "中风险": {}},
            "stats": {"total_detections": 0, "new_vocab_added": 0, "auto_added": 0}
        }
    
    def _load_config(self) -> AutoLearnConfig:
        """加载配置"""
        config_data = self._load_json(AUTO_LEARN_CONFIG_PATH, None)
        if config_data:
            return AutoLearnConfig(**config_data)
        return AutoLearnConfig()
    
    def _save_config(self):
        """保存配置"""
        self._save_json(AUTO_LEARN_CONFIG_PATH, {
            "auto_add_threshold": self.config.auto_add_threshold,
            "cleanup_days": self.config.cleanup_days,
            "min_frequency_to_keep": self.config.min_frequency_to_keep,
            "domain_sources": self.config.domain_sources,
            "last_auto_update": self.config.last_auto_update,
            "last_domain_expansion": self.config.last_domain_expansion,
        })
    
    # ============== 记录词汇出现 ==============
    
    def record_vocab_occurrence(self, vocabulary: str, context: str, risk_level: str = "待确认"):
        """记录词汇出现"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if vocabulary not in self.vocab_frequency:
            self.vocab_frequency[vocabulary] = {
                "count": 0,
                "first_seen": today,
                "last_seen": today,
                "contexts": [],
                "risk_level": risk_level,
                "auto_added": False
            }
        
        self.vocab_frequency[vocabulary]["count"] += 1
        self.vocab_frequency[vocabulary]["last_seen"] = today
        
        # 记录上下文（最多保留5个）
        if context and len(self.vocab_frequency[vocabulary]["contexts"]) < 5:
            self.vocab_frequency[vocabulary]["contexts"].append(context[:100])
        
        self._save_json(VOCAB_FREQUENCY_PATH, self.vocab_frequency)
        
        # 检查是否达到自动加入阈值
        self._check_auto_add(vocabulary)
    
    def _check_auto_add(self, vocabulary: str):
        """检查是否达到自动加入阈值"""
        if vocabulary in self.vocab_frequency:
            freq_data = self.vocab_frequency[vocabulary]
            
            # 达到阈值且未加入词库
            if freq_data["count"] >= self.config.auto_add_threshold and not freq_data["auto_added"]:
                # 根据上下文判断风险等级
                risk_level = self._determine_risk_level(vocabulary, freq_data["contexts"])
                
                # 加入词库
                self._add_to_vocab_db(vocabulary, risk_level, freq_data["contexts"])
                
                # 标记为已自动加入
                freq_data["auto_added"] = True
                self._save_json(VOCAB_FREQUENCY_PATH, self.vocab_frequency)
                
                print(f"✅ 自动加入词库：「{vocabulary}」→ {risk_level}")
    
    def _determine_risk_level(self, vocabulary: str, contexts: List[str]) -> str:
        """根据上下文判断风险等级"""
        # 高风险关键词
        high_risk_keywords = ["量子", "干细胞", "DNA", "基因", "石墨烯", "纳米", "根治", "包治", "保本", "稳赚"]
        
        # 中风险关键词
        medium_risk_keywords = ["模型", "算法", "免疫", "细胞", "肽"]
        
        vocab_lower = vocabulary.lower()
        
        for keyword in high_risk_keywords:
            if keyword in vocab_lower:
                return "极高风险"
        
        for keyword in medium_risk_keywords:
            if keyword in vocab_lower:
                return "高风险"
        
        return "中风险"
    
    def _add_to_vocab_db(self, vocabulary: str, risk_level: str, contexts: List[str]):
        """添加到词库"""
        if risk_level not in self.vocab_db["custom"]:
            self.vocab_db["custom"][risk_level] = {}
        
        self.vocab_db["custom"][risk_level][vocabulary] = {
            "正确语境": [],
            "伪科学场景": contexts[:3] if contexts else [],
            "auto_added": True,
            "added_time": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.vocab_db["stats"]["auto_added"] = self.vocab_db["stats"].get("auto_added", 0) + 1
        self._save_json(VOCABULARY_DB_PATH, self.vocab_db)
    
    # ============== 清理低价值词汇 ==============
    
    def cleanup_low_value_vocab(self):
        """清理低价值词汇"""
        today = datetime.now()
        cleanup_date = (today - timedelta(days=self.config.cleanup_days)).strftime("%Y-%m-%d")
        
        to_remove = []
        
        for vocab, data in self.vocab_frequency.items():
            # 未自动加入 且 出现次数少于阈值 且 长时间未出现
            if (not data["auto_added"] and 
                data["count"] < self.config.min_frequency_to_keep and 
                data["last_seen"] < cleanup_date):
                to_remove.append(vocab)
        
        # 删除低价值词汇
        for vocab in to_remove:
            del self.vocab_frequency[vocab]
            print(f"🗑️ 清理低价值词汇：「{vocab}」")
        
        if to_remove:
            self._save_json(VOCAB_FREQUENCY_PATH, self.vocab_frequency)
            self.config.last_auto_update = today.strftime("%Y-%m-%d")
            self._save_config()
        
        return len(to_remove)
    
    # ============== 自动扩展专业领域词汇 ==============
    
    def expand_domain_vocabulary(self, domain: str = None):
        """扩展专业领域词汇"""
        expanded_count = 0
        
        domains_to_expand = [domain] if domain else list(self.config.domain_sources.keys())
        
        for dom in domains_to_expand:
            if dom not in self.vocab_db["professional"]:
                self.vocab_db["professional"][dom] = {}
            
            source_vocabs = self.config.domain_sources.get(dom, [])
            
            for vocab in source_vocabs:
                # 检查是否已存在
                if vocab not in self.vocab_db["professional"][dom]:
                    self.vocab_db["professional"][dom][vocab] = {
                        "added_time": datetime.now().strftime("%Y-%m-%d"),
                        "source": "auto_expansion"
                    }
                    expanded_count += 1
                    print(f"📚 扩展领域词汇：「{vocab}」→ {dom}")
        
        if expanded_count > 0:
            self._save_json(VOCABULARY_DB_PATH, self.vocab_db)
            self.config.last_domain_expansion = datetime.now().strftime("%Y-%m-%d")
            self._save_config()
        
        return expanded_count
    
    def update_domain_sources_from_hot_topics(self, hot_topics: Dict[str, List[str]]):
        """从热点话题更新领域词汇源"""
        for domain, topics in hot_topics.items():
            if domain not in self.config.domain_sources:
                self.config.domain_sources[domain] = []
            
            for topic in topics:
                if topic not in self.config.domain_sources[domain]:
                    self.config.domain_sources[domain].append(topic)
                    print(f"🔥 新增热点词汇：「{topic}」→ {domain}")
        
        self._save_config()
    
    # ============== 统计报告 ==============
    
    def generate_stats_report(self) -> str:
        """生成统计报告"""
        report = []
        
        report.append("# 词库自动学习统计报告")
        report.append("")
        
        # 词汇频率统计
        total_vocabs = len(self.vocab_frequency)
        auto_added = len([v for v in self.vocab_frequency.values() if v.get("auto_added")])
        pending = len([v for v in self.vocab_frequency.values() if not v.get("auto_added")])
        
        report.append("## 词库统计")
        report.append("")
        report.append(f"| 项目 | 数量 |")
        report.append(f"|------|------|")
        report.append(f"| 总词汇数 | {total_vocabs} |")
        report.append(f"| 自动加入 | {auto_added} |")
        report.append(f"| 待确认 | {pending} |")
        report.append("")
        
        # 高频词汇
        sorted_vocabs = sorted(self.vocab_frequency.items(), key=lambda x: x[1]["count"], reverse=True)
        top_vocabs = sorted_vocabs[:10]
        
        if top_vocabs:
            report.append("## 高频词汇（TOP 10）")
            report.append("")
            report.append(f"| 词汇 | 出现次数 | 风险等级 | 状态 |")
            report.append(f"|------|----------|----------|------|")
            for vocab, data in top_vocabs:
                status = "✅ 已加入" if data.get("auto_added") else "⏳ 待确认"
                report.append(f"| {vocab} | {data['count']} | {data.get('risk_level', '未知')} | {status} |")
            report.append("")
        
        # 领域词汇覆盖
        report.append("## 领域词汇覆盖")
        report.append("")
        for domain, vocabs in self.vocab_db.get("professional", {}).items():
            count = len(vocabs)
            report.append(f"- {domain}：{count}个词汇")
        report.append("")
        
        # 配置信息
        report.append("## 配置信息")
        report.append("")
        report.append(f"- 自动加入阈值：{self.config.auto_add_threshold}次")
        report.append(f"- 清理周期：{self.config.cleanup_days}天")
        report.append(f"- 最低保留频率：{self.config.min_frequency_to_keep}次")
        report.append(f"- 最后自动更新：{self.config.last_auto_update or '未执行'}")
        report.append(f"- 最后领域扩展：{self.config.last_domain_expansion or '未执行'}")
        
        return "\n".join(report)
    
    # ============== 主执行函数 ==============
    
    def run_auto_learning(self):
        """执行自动学习流程"""
        print("="*60)
        print("🔄 词库自动学习系统启动")
        print("="*60)
        
        # 1. 清理低价值词汇
        print("\n📋 步骤1：清理低价值词汇")
        cleaned = self.cleanup_low_value_vocab()
        print(f"   清理了 {cleaned} 个低价值词汇")
        
        # 2. 扩展专业领域词汇
        print("\n📚 步骤2：扩展专业领域词汇")
        expanded = self.expand_domain_vocabulary()
        print(f"   扩展了 {expanded} 个领域词汇")
        
        # 3. 生成统计报告
        print("\n📊 步骤3：生成统计报告")
        report = self.generate_stats_report()
        print(report)
        
        print("\n" + "="*60)
        print("✅ 自动学习完成")
        print("="*60)


# ============== 命令行入口 ==============

if __name__ == "__main__":
    import sys
    
    learner = VocabAutoLearner()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "run":
            # 执行完整自动学习流程
            learner.run_auto_learning()
        
        elif cmd == "stats":
            # 查看统计
            print(learner.generate_stats_report())
        
        elif cmd == "cleanup":
            # 清理低价值词汇
            cleaned = learner.cleanup_low_value_vocab()
            print(f"✅ 清理了 {cleaned} 个低价值词汇")
        
        elif cmd == "expand":
            # 扩展领域词汇
            domain = sys.argv[2] if len(sys.argv) > 2 else None
            expanded = learner.expand_domain_vocabulary(domain)
            print(f"✅ 扩展了 {expanded} 个领域词汇")
        
        elif cmd == "record":
            # 记录词汇出现
            vocab = sys.argv[2] if len(sys.argv) > 2 else None
            if vocab:
                learner.record_vocab_occurrence(vocab, "")
                print(f"✅ 已记录词汇：「{vocab}」")
        
        else:
            print(f"未知命令：{cmd}")
            print("可用命令：run（执行学习）、stats（统计）、cleanup（清理）、expand（扩展）、record（记录）")
    
    else:
        # 默认执行完整流程
        learner.run_auto_learning()
