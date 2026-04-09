#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI内容幻觉检测器 - 自动化检测脚本 v1.4.0
功能: 自动提取高风险内容、科学词汇检测、逻辑冲突识别、词汇库自动扩展、权威总结生成、出处自动核验、报告摘要、词库自动学习
"""

import re
import json
import os
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field, asdict
from collections import Counter
from datetime import datetime

# ============== 配置 ==============

# 词汇库文件路径（相对于脚本所在目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
VOCABULARY_DB_PATH = os.path.join(DATA_DIR, "vocabulary_db.json")
NEW_VOCABULARY_PATH = os.path.join(DATA_DIR, "new_vocabulary_found.json")
DETECTION_HISTORY_PATH = os.path.join(DATA_DIR, "detection_history.json")
VOCAB_FREQUENCY_PATH = os.path.join(DATA_DIR, "vocab_frequency.json")

# 高频科学词汇库（按风险等级分类）
SCIENTIFIC_VOCABULARY = {
    "极高风险": {
        "量子": {"正确语境": ["量子计算", "量子通信", "量子力学", "量子物理"], "伪科学场景": ["量子养生", "量子水", "量子医学", "量子能量"]},
        "干细胞": {"正确语境": ["再生医学", "临床治疗", "干细胞研究"], "伪科学场景": ["干细胞美容", "干细胞保健品", "干细胞养生"]},
        "DNA": {"正确语境": ["遗传学", "基因检测", "分子生物学"], "伪科学场景": ["DNA修复", "DNA激活", "DNA美容"]},
        "基因": {"正确语境": ["基因工程", "遗传学", "基因编辑"], "伪科学场景": ["基因修复", "基因激活", "基因养生"]},
        "石墨烯": {"正确语境": ["材料科学", "电子器件", "新能源"], "伪科学场景": ["石墨烯内衣", "石墨烯床垫", "石墨烯保健"]},
        "同位素": {"正确语境": ["核医学", "核化学", "放射性"], "伪科学场景": ["同位素养生", "同位素能量"]},
        "辐射": {"正确语境": ["核物理", "医学影像", "放疗"], "伪科学场景": ["辐射调理", "辐射能量", "辐射养生"]},
    },
    "高风险": {
        "原子": {"正确语境": ["原子物理", "原子能", "原子结构"], "伪科学场景": ["原子能量", "原子养生"]},
        "粒子": {"正确语境": ["粒子物理", "基本粒子", "高能物理"], "伪科学场景": ["粒子修复", "粒子能量"]},
        "纳米": {"正确语境": ["纳米技术", "材料科学", "纳米材料"], "伪科学场景": ["纳米养生", "纳米美容", "纳米保健"]},
        "细胞": {"正确语境": ["细胞生物学", "医学", "细胞治疗"], "伪科学场景": ["细胞再生", "细胞激活", "细胞养生"]},
        "免疫": {"正确语境": ["免疫学", "医学", "免疫治疗"], "伪科学场景": ["免疫激活", "免疫调理", "免疫养生"]},
        "靶向": {"正确语境": ["靶向治疗", "医学", "药物研发"], "伪科学场景": ["靶向养生", "靶向修复"]},
        "磁场": {"正确语境": ["电磁学", "地球物理", "MRI"], "伪科学场景": ["磁场调理", "磁场养生", "磁场疗愈"]},
        "端粒": {"正确语境": ["分子生物学", "衰老研究"], "伪科学场景": ["端粒延长", "端粒激活"]},
        "肽": {"正确语境": ["生物化学", "医学", "蛋白质研究"], "伪科学场景": ["活性肽", "肽能量", "肽养生"]},
    },
    "中风险": {
        "模型": {"正确语境": ["机器学习", "AI", "数学建模"], "伪科学场景": ["智能模型（万能效果）"]},
        "算法": {"正确语境": ["计算机科学", "数据分析"], "伪科学场景": ["算法养生", "算法调理"]},
        "神经网络": {"正确语境": ["深度学习", "AI"], "伪科学场景": ["神经网络激活（非技术语境）"]},
        "蛋白质": {"正确语境": ["生物化学", "营养学"], "伪科学场景": ["蛋白质激活", "蛋白质能量"]},
        "酶": {"正确语境": ["生物化学", "医学"], "伪科学场景": ["酶激活", "酶能量"]},
        "分子": {"正确语境": ["化学", "分子生物学"], "伪科学场景": ["分子能量", "分子调理"]},
    },
}

# 专业领域词汇库（新增）
PROFESSIONAL_VOCABULARY = {
    "金融": {
        "极高风险": ["内幕消息", "稳赚不赔", "保本保息", "年化收益100%"],
        "高风险": ["暴涨", "暴涨必买", "庄家拉升", "内幕票"],
        "中风险": ["投资建议", "理财推荐", "收益预测"],
    },
    "法律": {
        "极高风险": ["包赢", "必胜诉", "关系硬", "特殊渠道"],
        "中风险": ["法律意见", "风险评估"],
    },
    "医疗": {
        "极高风险": ["根治", "百分百治愈", "包治", "无副作用", "祖传秘方"],
        "高风险": ["疗效显著", "药到病除", "专家推荐"],
        "中风险": ["治疗效果", "临床验证"],
    },
    "教育": {
        "极高风险": ["保过", "包录取", "内部名额", "真题泄露"],
        "高风险": ["速成", "7天精通", "零基础高薪"],
        "中风险": ["课程效果", "学习成果"],
    },
}

# 伪科学产品关键词组合
PSEUDOSCIENCE_PATTERNS = [
    r"量子.{0,5}(水|杯|袜|衣|垫|枕|手环|项链|能量|养生)",
    r"纳米.{0,5}(内衣|床垫|袜子|保健|养生|美容)",
    r"干细胞.{0,5}(美容|保健品|养生|护肤)",
    r"DNA.{0,5}(修复|激活|美容|护肤)",
    r"基因.{0,5}(修复|激活|养生|美容)",
    r"石墨烯.{0,5}(内衣|床垫|保健|养生)",
    r"能量.{0,5}(场|波|共振|调理)",
    r"磁.{0,5}(场.{0,5}调理|疗愈|养生)",
    r"端粒.{0,5}(延长|激活|逆转)",
]

# 数据提取正则
DATA_PATTERNS = {
    "金额": r"(\d+(?:\.\d+)?)\s*(亿|万|千|百|元)(?:美元|人民币)?",
    "百分比": r"(\d+(?:\.\d+)?)\s*[%％]",
    "增长率": r"(?:增长|同比|环比|增幅)(?:\d+(?:\.\d+)?)?\s*[%％]|(\d+(?:\.\d+)?)\s*[%％].*?增长",
    "数量": r"(\d+(?:\.\d+)?)\s*(家|个|人|次|件|项|条|本|册|款|种|类)",
    "日期": r"(\d{4})年(\d{1,2})月(\d{1,2})[日号]?|(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})",
    "时间": r"(\d{1,2})[时点](\d{1,2})?分?|(\d{1,2}):(\d{1,2})",
}

# 范围性关键词
SCOPE_KEYWORDS = ["全国", "全球", "全行业", "全部", "所有", "整体", "总计", "共计", "全面", "完整"]

# 引用来源关键词
SOURCE_KEYWORDS = ["根据", "据", "报道称", "报道", "数据显示", "专家指出", "研究表明", "文件", "报告", "意见", "通知", "办法", "规定", "条例"]

# 绝对化表述
ABSOLUTE_EXPRESSIONS = ["一定", "必定", "肯定", "绝对", "必然", "所有", "全部", "完全", "彻底", "根本", "永远"]

# 因果逻辑关键词
CAUSAL_KEYWORDS = ["导致", "引起", "造成", "使得", "促使", "引发", "带来", "产生"]


# ============== 数据结构 ==============

@dataclass
class RiskItem:
    """风险项"""
    type: str
    content: str
    risk_level: str
    description: str
    suggestion: str
    position: Tuple[int, int] = (0, 0)


@dataclass
class VocabularyFound:
    """发现的词汇"""
    vocabulary: str
    context: str
    risk_level: str
    is_correct_context: bool
    is_new: bool = False
    found_time: str = ""


@dataclass
class DetectionResult:
    """检测结果"""
    text_length: int = 0
    text_type: str = "unknown"
    risk_items: List[RiskItem] = field(default_factory=list)
    scientific_vocab: Dict[str, List[VocabularyFound]] = field(default_factory=dict)
    professional_vocab: Dict[str, List[VocabularyFound]] = field(default_factory=dict)
    logic_conflicts: List[str] = field(default_factory=list)
    pseudoscience_detected: List[str] = field(default_factory=list)
    new_vocabulary: List[VocabularyFound] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)
    authoritative_summary: str = ""


# ============== 词汇库管理 ==============

class VocabularyDB:
    """词汇库管理器（v1.4.0增加自动学习功能）"""
    
    def __init__(self):
        self.db = self._load_db()
        self.new_vocab = self._load_new_vocab()
        self.vocab_frequency = self._load_vocab_frequency()
        self.auto_add_threshold = 3  # 出现3次自动加入
    
    def _load_db(self) -> Dict:
        """加载词汇库"""
        if os.path.exists(VOCABULARY_DB_PATH):
            try:
                with open(VOCABULARY_DB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {
            "scientific": SCIENTIFIC_VOCABULARY,
            "professional": PROFESSIONAL_VOCABULARY,
            "custom": {"极高风险": {}, "高风险": {}, "中风险": {}},
            "stats": {"total_detections": 0, "new_vocab_added": 0, "auto_added": 0}
        }
    
    def _load_new_vocab(self) -> List:
        """加载新发现的词汇"""
        if os.path.exists(NEW_VOCABULARY_PATH):
            try:
                with open(NEW_VOCABULARY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _load_vocab_frequency(self) -> Dict:
        """加载词汇频率"""
        if os.path.exists(VOCAB_FREQUENCY_PATH):
            try:
                with open(VOCAB_FREQUENCY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_db(self):
        """保存词汇库"""
        os.makedirs(os.path.dirname(VOCABULARY_DB_PATH), exist_ok=True)
        with open(VOCABULARY_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
    
    def save_new_vocab(self):
        """保存新发现的词汇"""
        os.makedirs(os.path.dirname(NEW_VOCABULARY_PATH), exist_ok=True)
        with open(NEW_VOCABULARY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.new_vocab, f, ensure_ascii=False, indent=2)
    
    def save_vocab_frequency(self):
        """保存词汇频率"""
        os.makedirs(os.path.dirname(VOCAB_FREQUENCY_PATH), exist_ok=True)
        with open(VOCAB_FREQUENCY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.vocab_frequency, f, ensure_ascii=False, indent=2)
    
    def add_new_vocabulary(self, vocab: VocabularyFound):
        """添加新发现的词汇"""
        vocab.found_time = datetime.now().isoformat()
        self.new_vocab.append(asdict(vocab))
        self.save_new_vocab()
        
        # v1.4.0新增：记录词汇频率
        self._record_vocab_frequency(vocab.vocabulary, vocab.context, vocab.risk_level)
    
    def _record_vocab_frequency(self, vocabulary: str, context: str, risk_level: str):
        """记录词汇出现频率"""
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
        
        self.save_vocab_frequency()
        
        # 检查是否达到自动加入阈值
        self._check_auto_add(vocabulary)
    
    def _check_auto_add(self, vocabulary: str):
        """检查是否达到自动加入阈值"""
        if vocabulary in self.vocab_frequency:
            freq_data = self.vocab_frequency[vocabulary]
            
            # 达到阈值且未加入词库
            if freq_data["count"] >= self.auto_add_threshold and not freq_data["auto_added"]:
                # 根据上下文判断风险等级
                risk_level = self._determine_risk_level(vocabulary, freq_data["contexts"])
                
                # 加入词库
                self._auto_add_to_vocab_db(vocabulary, risk_level, freq_data["contexts"])
                
                # 标记为已自动加入
                freq_data["auto_added"] = True
                self.save_vocab_frequency()
    
    def _determine_risk_level(self, vocabulary: str, contexts: List[str]) -> str:
        """根据上下文判断风险等级"""
        high_risk_keywords = ["量子", "干细胞", "DNA", "基因", "石墨烯", "纳米", "根治", "包治", "保本", "稳赚"]
        medium_risk_keywords = ["模型", "算法", "免疫", "细胞", "肽"]
        
        vocab_lower = vocabulary.lower()
        
        for keyword in high_risk_keywords:
            if keyword in vocab_lower:
                return "极高风险"
        
        for keyword in medium_risk_keywords:
            if keyword in vocab_lower:
                return "高风险"
        
        return "中风险"
    
    def _auto_add_to_vocab_db(self, vocabulary: str, risk_level: str, contexts: List[str]):
        """自动添加到词库"""
        if risk_level not in self.db["custom"]:
            self.db["custom"][risk_level] = {}
        
        self.db["custom"][risk_level][vocabulary] = {
            "正确语境": [],
            "伪科学场景": contexts[:3] if contexts else [],
            "auto_added": True,
            "added_time": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.db["stats"]["auto_added"] = self.db["stats"].get("auto_added", 0) + 1
        self.save_db()
    
    def update_stats(self, detection_count: int):
        """更新统计"""
        self.db["stats"]["total_detections"] += detection_count
        self.save_db()
    
    def get_all_scientific_vocab(self) -> Set[str]:
        """获取所有科学词汇"""
        all_vocab = set()
        for risk_level, vocabs in self.db["scientific"].items():
            all_vocab.update(vocabs.keys())
        for risk_level, vocabs in self.db["custom"].items():
            all_vocab.update(vocabs.keys())
        return all_vocab
    
    def is_known_vocab(self, vocab: str) -> bool:
        """检查是否是已知词汇"""
        return vocab in self.get_all_scientific_vocab()


# ============== 核心检测函数 ==============

def detect_text_type(text: str) -> str:
    """判断文本类型"""
    if len(text) < 200:
        return "short"
    elif len(text) < 500:
        return "medium"
    else:
        return "long"


def extract_data_content(text: str) -> List[Dict]:
    """提取数据类内容"""
    results = []
    for data_type, pattern in DATA_PATTERNS.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            results.append({
                "type": data_type,
                "content": match.group(),
                "position": match.span()
            })
    return results


def extract_scope_content(text: str) -> List[Dict]:
    """提取范围性内容"""
    results = []
    for keyword in SCOPE_KEYWORDS:
        pattern = rf"{keyword}[^。！？\n]{{0,50}}"
        matches = re.finditer(pattern, text)
        for match in matches:
            results.append({
                "keyword": keyword,
                "content": match.group(),
                "position": match.span()
            })
    return results


def extract_source_content(text: str) -> List[Dict]:
    """提取引用类内容"""
    results = []
    for keyword in SOURCE_KEYWORDS:
        pattern = rf"{keyword}[^。！？\n]{{0,100}}"
        matches = re.finditer(pattern, text)
        for match in matches:
            results.append({
                "keyword": keyword,
                "content": match.group(),
                "position": match.span()
            })
    return results


def detect_scientific_vocabulary(text: str, vocab_db: VocabularyDB) -> Tuple[Dict[str, List[VocabularyFound]], List[VocabularyFound]]:
    """检测科学词汇，返回发现结果和新词汇"""
    found_vocab = {"极高风险": [], "高风险": [], "中风险": []}
    new_vocab_list = []
    
    for risk_level, vocab_dict in vocab_db.db["scientific"].items():
        for vocab, context_info in vocab_dict.items():
            if vocab in text:
                pattern = rf"{vocab}[^。！？\n]{{0,30}}"
                matches = re.findall(pattern, text)
                for match in matches:
                    correct_contexts = context_info.get("正确语境", [])
                    pseudoscience_contexts = context_info.get("伪科学场景", [])
                    
                    is_correct = any(ctx in match for ctx in correct_contexts)
                    is_pseudoscience = any(ctx in match for ctx in pseudoscience_contexts)
                    
                    vocab_found = VocabularyFound(
                        vocabulary=vocab,
                        context=match,
                        risk_level=risk_level,
                        is_correct_context=is_correct and not is_pseudoscience,
                        is_new=False
                    )
                    found_vocab[risk_level].append(vocab_found)
    
    # 检查是否有新词汇（v1.3.1优化：改进正则，过滤误识别）
    # 只匹配科学/技术类术语，排除常见词和误识别
    potential_terms = re.findall(r'([\u4e00-\u9fa5]{2,4})(?:技术|疗法|原理|效应|机制|系统|模型|算法)', text)
    
    # 过滤条件
    stop_words = ['指出', '表明', '说明', '发现', '研究', '表示', '认为', '提出', '该技术', '本技术']
    
    for term in potential_terms:
        # 过滤：长度<2、包含停用词、纯数字开头的
        if len(term) < 2:
            continue
        if any(sw in term for sw in stop_words):
            continue
        if term[0].isdigit():
            continue
        
        if not vocab_db.is_known_vocab(term):
            new_vocab = VocabularyFound(
                vocabulary=term,
                context=text[max(0, text.find(term)-20):text.find(term)+len(term)+20],
                risk_level="待确认",
                is_correct_context=False,
                is_new=True
            )
            new_vocab_list.append(new_vocab)
            vocab_db.add_new_vocabulary(new_vocab)
    
    return found_vocab, new_vocab_list


def detect_professional_vocabulary(text: str) -> Dict[str, List[VocabularyFound]]:
    """检测专业领域词汇"""
    found_vocab = {}
    
    for domain, risk_levels in PROFESSIONAL_VOCABULARY.items():
        found_vocab[domain] = []
        for risk_level, vocabs in risk_levels.items():
            for vocab in vocabs:
                if vocab in text:
                    pattern = rf"[^。！？\n]{{0,20}}{vocab}[^。！？\n]{{0,20}}"
                    matches = re.findall(pattern, text)
                    for match in matches:
                        found_vocab[domain].append(VocabularyFound(
                            vocabulary=vocab,
                            context=match,
                            risk_level=risk_level,
                            is_correct_context=False
                        ))
    
    return found_vocab


def detect_pseudoscience(text: str) -> List[str]:
    """检测伪科学营销"""
    detected = []
    for pattern in PSEUDOSCIENCE_PATTERNS:
        matches = re.findall(pattern, text)
        detected.extend(matches)
    return detected


def detect_logic_conflicts(text: str) -> List[str]:
    """检测逻辑冲突"""
    conflicts = []
    
    # 数值矛盾
    numbers = re.findall(r"(\d+(?:\.\d+)?)", text)
    if len(set(numbers)) < len(numbers):
        conflicts.append("检测到重复数值，建议核实是否一致")
    
    # 时间矛盾
    dates = re.findall(r"(\d{4})年", text)
    if len(dates) > 1:
        years = [int(d) for d in dates]
        if max(years) - min(years) > 10:
            conflicts.append(f"时间跨度较大（{min(years)}-{max(years)}），建议核实时间线")
    
    # 因果冲突
    for word in CAUSAL_KEYWORDS:
        if word in text:
            conflicts.append(f"检测到因果表述「{word}」，建议核实因果关系是否成立")
    
    # 绝对化表述
    for word in ABSOLUTE_EXPRESSIONS:
        if word in text:
            conflicts.append(f"检测到绝对化表述「{word}」，建议核实是否有充分依据")
    
    return conflicts


def detect_complex_logic_short(text: str) -> List[str]:
    """短文本复杂逻辑检测"""
    issues = []
    
    if text.count("因为") > 1 or text.count("所以") > 1:
        issues.append("多层因果逻辑，建议逐步验证每个环节")
    
    if text.count("如果") > 1 or text.count("那么") > 1:
        issues.append("多层条件逻辑，建议验证条件是否完整")
    
    if text.count("但是") > 1 or text.count("然而") > 1:
        issues.append("多次转折，建议核实前后表述是否矛盾")
    
    if text.count("和") > 3 or text.count("以及") > 2:
        issues.append("多项并列，建议核实是否完整列举")
    
    return issues


# ============== 权威总结生成 ==============

def generate_authoritative_summary(result: DetectionResult) -> str:
    """生成权威总结"""
    summary_parts = []
    
    # 1. 总体评估
    total_risks = result.statistics.get("总风险项", 0)
    high_risks = result.statistics.get("高风险", 0)
    
    if high_risks >= 5:
        risk_level = "⚠️ **高风险内容**"
        risk_desc = "该文本存在多处高风险问题，建议谨慎采用或全面核实后使用。"
    elif high_risks >= 2:
        risk_level = "⚡ **中等风险内容**"
        risk_desc = "该文本存在部分高风险问题，建议针对标注内容进行核实。"
    else:
        risk_level = "✅ **低风险内容**"
        risk_desc = "该文本整体风险较低，但仍建议核实关键数据。"
    
    summary_parts.append(f"## 总体评估\n\n{risk_level}\n\n{risk_desc}")
    
    # 2. 核心问题分析
    summary_parts.append("## 核心问题分析")
    
    # 科学词汇问题
    if any(result.scientific_vocab.values()):
        summary_parts.append("\n### 科学词汇问题")
        for risk_level, vocabs in result.scientific_vocab.items():
            if vocabs:
                pseudoscience_vocabs = [v for v in vocabs if not v.is_correct_context]
                if pseudoscience_vocabs:
                    summary_parts.append(f"\n**{risk_level}词汇（{len(pseudoscience_vocabs)}个）可能存在滥用**：")
                    for v in pseudoscience_vocabs[:3]:  # 只显示前3个
                        summary_parts.append(f"- 「{v.vocabulary}」：{v.context}")
                        summary_parts.append(f"  - 建议：核实是否有科学文献支持，或标注「缺乏科学依据」")
    
    # 专业领域问题
    if any(result.professional_vocab.values()):
        summary_parts.append("\n### 专业领域问题")
        for domain, vocabs in result.professional_vocab.items():
            if vocabs:
                high_risk_vocabs = [v for v in vocabs if v.risk_level in ["极高风险", "高风险"]]
                if high_risk_vocabs:
                    summary_parts.append(f"\n**{domain}领域**发现{len(high_risk_vocabs)}个高风险表述：")
                    for v in high_risk_vocabs[:3]:
                        summary_parts.append(f"- 「{v.vocabulary}」：{v.context}")
    
    # 伪科学问题
    if result.pseudoscience_detected:
        summary_parts.append("\n### 伪科学营销问题")
        summary_parts.append(f"\n⚠️ 检测到 **{len(result.pseudoscience_detected)}** 条疑似伪科学表述：")
        for pseudo in result.pseudoscience_detected[:3]:
            summary_parts.append(f"- ❌ 「{pseudo}」")
        summary_parts.append("\n**权威建议**：此类表述缺乏科学依据，建议删除或标注「该说法未经科学验证」。")
    
    # 数据问题
    data_risks = [r for r in result.risk_items if r.type == "数据"]
    if data_risks:
        summary_parts.append("\n### 数据核验问题")
        summary_parts.append(f"\n发现 **{len(data_risks)}** 处数据需要核实：")
        for r in data_risks[:3]:
            summary_parts.append(f"- 「{r.content}」：{r.suggestion}")
        summary_parts.append("\n**核验建议**：")
        summary_parts.append("- 查找官方数据来源（政府官网、权威报告）")
        summary_parts.append("- 交叉验证多个来源的数据一致性")
        summary_parts.append("- 标注数据出处和时间")
    
    # 逻辑问题
    if result.logic_conflicts:
        summary_parts.append("\n### 逻辑问题")
        for conflict in result.logic_conflicts[:3]:
            summary_parts.append(f"- ⚠️ {conflict}")
    
    # 3. 行动建议
    summary_parts.append("\n## 行动建议")
    
    actions = []
    if high_risks >= 3:
        actions.append("1. **优先处理高风险项**：先核实科学词汇和数据来源")
    if result.pseudoscience_detected:
        actions.append("2. **删除伪科学表述**：避免误导读者，影响可信度")
    if data_risks:
        actions.append("3. **标注数据来源**：为所有数据添加官方出处")
    if any(result.scientific_vocab.values()):
        actions.append("4. **核实科学术语**：确认专业术语是否在正确语境中使用")
    
    if actions:
        summary_parts.append("\n" + "\n".join(actions))
    else:
        summary_parts.append("\n该文本整体可信度较高，建议进行常规核实即可。")
    
    # 4. 新词汇发现（如果有）
    if result.new_vocabulary:
        summary_parts.append("\n## 新词汇发现")
        summary_parts.append(f"\n本次检测发现 **{len(result.new_vocabulary)}** 个潜在专业术语，已记录待人工确认：")
        for v in result.new_vocabulary[:5]:
            summary_parts.append(f"- 「{v.vocabulary}」：{v.context}")
        summary_parts.append("\n> 这些词汇将在人工确认后加入词汇库，持续优化检测能力。")
    
    return "\n".join(summary_parts)


# ============== 主检测函数 ==============

def analyze_text(text: str, vocab_db: Optional[VocabularyDB] = None) -> DetectionResult:
    """分析文本"""
    if vocab_db is None:
        vocab_db = VocabularyDB()
    
    result = DetectionResult()
    result.text_length = len(text)
    result.text_type = detect_text_type(text)
    
    # 1. 数据类检测
    data_items = extract_data_content(text)
    for item in data_items:
        result.risk_items.append(RiskItem(
            type="数据",
            content=item["content"],
            risk_level="高",
            description=f"检测到{item['type']}数据",
            suggestion="核实数据来源和准确性",
            position=item["position"]
        ))
    
    # 2. 范围类检测
    scope_items = extract_scope_content(text)
    for item in scope_items:
        result.risk_items.append(RiskItem(
            type="范围",
            content=item["content"],
            risk_level="高",
            description=f"检测到范围性表述「{item['keyword']}」",
            suggestion="逐项核实覆盖范围是否完整",
            position=item["position"]
        ))
    
    # 3. 引用类检测
    source_items = extract_source_content(text)
    for item in source_items:
        result.risk_items.append(RiskItem(
            type="引用",
            content=item["content"],
            risk_level="中",
            description=f"检测到引用表述「{item['keyword']}」",
            suggestion="核实引用来源是否真实可追溯",
            position=item["position"]
        ))
    
    # 4. 科学词汇检测
    result.scientific_vocab, result.new_vocabulary = detect_scientific_vocabulary(text, vocab_db)
    
    for risk_level, vocabs in result.scientific_vocab.items():
        for vocab_info in vocabs:
            if not vocab_info.is_correct_context:
                result.risk_items.append(RiskItem(
                    type="科学词汇",
                    content=vocab_info.context,
                    risk_level="高" if risk_level == "极高风险" else "中",
                    description=f"检测到科学词汇「{vocab_info.vocabulary}」可能存在滥用",
                    suggestion="核实是否在正确科学语境中使用",
                ))
    
    # 5. 专业领域词汇检测
    result.professional_vocab = detect_professional_vocabulary(text)
    
    for domain, vocabs in result.professional_vocab.items():
        for vocab_info in vocabs:
            if vocab_info.risk_level in ["极高风险", "高风险"]:
                result.risk_items.append(RiskItem(
                    type=f"专业领域-{domain}",
                    content=vocab_info.context,
                    risk_level="高" if vocab_info.risk_level == "极高风险" else "中",
                    description=f"检测到{domain}领域「{vocab_info.vocabulary}」",
                    suggestion="核实是否有专业依据",
                ))
    
    # 6. 伪科学检测
    result.pseudoscience_detected = detect_pseudoscience(text)
    for pseudo in result.pseudoscience_detected:
        result.risk_items.append(RiskItem(
            type="伪科学",
            content=pseudo,
            risk_level="高",
            description="检测到疑似伪科学营销表述",
            suggestion="核实是否有科学依据，或标注缺乏科学支撑"
        ))
    
    # 7. 逻辑冲突检测
    result.logic_conflicts = detect_logic_conflicts(text)
    for conflict in result.logic_conflicts:
        result.risk_items.append(RiskItem(
            type="逻辑",
            content="",
            risk_level="中",
            description=conflict,
            suggestion="核实逻辑关系是否正确"
        ))
    
    # 8. 短文本复杂逻辑检测
    if result.text_type == "short":
        short_logic_issues = detect_complex_logic_short(text)
        for issue in short_logic_issues:
            result.risk_items.append(RiskItem(
                type="复杂逻辑",
                content="",
                risk_level="中",
                description=issue,
                suggestion="逐步验证每个逻辑环节"
            ))
    
    # 9. 统计信息
    result.statistics = {
        "总风险项": len(result.risk_items),
        "高风险": len([r for r in result.risk_items if r.risk_level == "高"]),
        "中风险": len([r for r in result.risk_items if r.risk_level == "中"]),
        "科学词汇": sum(len(v) for v in result.scientific_vocab.values()),
        "专业领域": sum(len(v) for v in result.professional_vocab.values()),
        "伪科学": len(result.pseudoscience_detected),
        "逻辑问题": len(result.logic_conflicts),
        "新词汇": len(result.new_vocabulary),
    }
    
    # 10. 生成权威总结
    result.authoritative_summary = generate_authoritative_summary(result)
    
    # 11. 更新词汇库统计
    vocab_db.update_stats(1)
    
    return result


def generate_report(result: DetectionResult) -> str:
    """生成检测报告"""
    report = []
    
    report.append("# AI内容幻觉检测报告")
    report.append("")
    
    # 概览
    report.append("## 检测概览")
    report.append("")
    report.append(f"| 项目 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 文本长度 | {result.text_length}字 |")
    report.append(f"| 文本类型 | {'短文本' if result.text_type == 'short' else '中长文本' if result.text_type == 'medium' else '长文本'} |")
    for key, value in result.statistics.items():
        report.append(f"| {key} | {value} |")
    report.append("")
    
    # 权威总结
    report.append(result.authoritative_summary)
    report.append("")
    
    # 核验清单
    report.append("## 核验清单")
    report.append("")
    check_items = [
        "核对数据来源",
        "验证数值单位",
        "确认范围完整性",
        "追溯引用出处",
        "核实科学词汇语境",
        "识别伪科学营销",
        "检查逻辑一致性",
    ]
    for item in check_items:
        report.append(f"- [ ] {item}")
    report.append("")
    
    report.append("---")
    report.append(f"*本报告由 AI内容幻觉检测器 v1.4.0 自动生成*")
    report.append(f"*检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(report)


# ============== 出处核验模块（v1.3.0新增）==============

@dataclass
class VerificationResult:
    """核验结果"""
    query: str  # 核验内容
    status: str  # 已验证/存疑/未找到
    sources: List[str]  # 来源列表
    confidence: float  # 可信度 0-1
    notes: str  # 备注


def extract_verification_targets(text: str) -> List[Dict]:
    """提取需要核验的目标"""
    targets = []
    
    # 1. 政策文件名称
    policy_pattern = r"《([^》]+)》"
    policy_matches = re.findall(policy_pattern, text)
    for match in policy_matches:
        targets.append({
            "type": "政策文件",
            "content": match,
            "search_query": f"{match} 官方文件"
        })
    
    # 2. 数据来源（金额+单位组合）
    data_pattern = r"(\d+(?:\.\d+)?)\s*(亿|万|千)(?:元)?"
    data_matches = re.findall(data_pattern, text)
    for match in data_matches:
        # 提取上下文
        context_pattern = rf"[^。！？\n]{{0,30}}{match[0]}\s*{match[1]}[^。！？\n]{{0,30}}"
        context_matches = re.findall(context_pattern, text)
        for ctx in context_matches:
            targets.append({
                "type": "数据",
                "content": f"{match[0]}{match[1]}",
                "search_query": ctx[:50]
            })
    
    # 3. 专家名称（v1.3.1优化：正确识别完整姓名）
    # 匹配：机构+姓名+头衔 或 姓名+头衔
    expert_pattern = r"(?:据|据|据)?([\u4e00-\u9fa5]{2,10}(?:大学|学院|研究院|医院)?)([\u4e00-\u9fa5]{2,4})(?:教授|专家|博士|院士|主任|院长)"
    expert_matches = re.findall(expert_pattern, text)
    for org, name in expert_matches:
        full_name = f"{org}{name}"
        targets.append({
            "type": "人物",
            "content": full_name,
            "search_query": f"{full_name} 教授"
        })
    
    # 单独的专家名（没有机构前缀）
    simple_expert_pattern = r"(?<!大学)(?<!学院)(?<!研究院)([\u4e00-\u9fa5]{2,4})(?:教授|专家|博士|院士|主任|院长)"
    simple_expert_matches = re.findall(simple_expert_pattern, text)
    for name in simple_expert_matches:
        if not any(name in t['content'] for t in targets):  # 避免重复
            targets.append({
                "type": "人物",
                "content": name,
                "search_query": f"{name} 教授 专家"
            })
    
    # 4. 机构名称（v1.3.1优化：排除误识别）
    org_pattern = r"(?<!据)(?<!据)([\u4e00-\u9fa5]{2,8})(?:研究院|研究所|大学|学院|医院|公司|集团)"
    org_matches = re.findall(org_pattern, text)
    for match in org_matches:
        # 过滤太短的匹配
        if len(match) < 2:
            continue
        targets.append({
            "type": "机构",
            "content": match,
            "search_query": f"{match} 官网"
        })
    
    # 去重
    seen = set()
    unique_targets = []
    for t in targets:
        key = f"{t['type']}-{t['content']}"
        if key not in seen:
            seen.add(key)
            unique_targets.append(t)
    
    return unique_targets


def verify_with_search_api(query: str, search_api_func=None) -> VerificationResult:
    """
    使用搜索API核验
    search_api_func: 可选的搜索函数，签名为 func(query: str) -> List[str]
    """
    if search_api_func is None:
        # 没有提供搜索API，返回待手动核验
        return VerificationResult(
            query=query,
            status="待核验",
            sources=[],
            confidence=0.0,
            notes="需手动搜索核验，建议使用：百度、Google、官方渠道"
        )
    
    try:
        results = search_api_func(query)
        if results:
            return VerificationResult(
                query=query,
                status="已验证",
                sources=results[:3],  # 只保留前3个来源
                confidence=0.8 if len(results) > 1 else 0.5,
                notes=f"找到 {len(results)} 个相关来源"
            )
        else:
            return VerificationResult(
                query=query,
                status="未找到",
                sources=[],
                confidence=0.0,
                notes="未找到相关来源，可能是虚构内容"
            )
    except Exception as e:
        return VerificationResult(
            query=query,
            status="核验失败",
            sources=[],
            confidence=0.0,
            notes=f"搜索出错：{str(e)}"
        )


def verify_content(text: str, search_api_func=None) -> List[VerificationResult]:
    """
    核验文本中的关键内容
    search_api_func: 可选的搜索函数，用于自动核验
    """
    targets = extract_verification_targets(text)
    results = []
    
    for target in targets[:10]:  # 最多核验10个目标
        result = verify_with_search_api(target["search_query"], search_api_func)
        result.query = f"{target['type']}：{target['content']}"
        results.append(result)
    
    return results


def generate_verification_report(results: List[VerificationResult]) -> str:
    """生成核验报告"""
    report = []
    
    report.append("## 出处核验报告")
    report.append("")
    
    # 统计
    verified = len([r for r in results if r.status == "已验证"])
    pending = len([r for r in results if r.status == "待核验"])
    not_found = len([r for r in results if r.status == "未找到"])
    
    report.append(f"| 状态 | 数量 |")
    report.append(f"|------|------|")
    report.append(f"| ✅ 已验证 | {verified} |")
    report.append(f"| ⏳ 待核验 | {pending} |")
    report.append(f"| ❌ 未找到 | {not_found} |")
    report.append("")
    
    # 详细结果
    for result in results:
        status_icon = {
            "已验证": "✅",
            "待核验": "⏳",
            "未找到": "❌",
            "核验失败": "⚠️"
        }.get(result.status, "❓")
        
        report.append(f"### {status_icon} {result.query}")
        report.append(f"- **状态**：{result.status}")
        report.append(f"- **可信度**：{result.confidence*100:.0f}%")
        
        if result.sources:
            report.append(f"- **来源**：")
            for src in result.sources[:2]:
                report.append(f"  - {src}")
        
        report.append(f"- **备注**：{result.notes}")
        report.append("")
    
    # 建议
    report.append("### 核验建议")
    if not_found > 0:
        report.append("- ⚠️ 存在未找到来源的内容，建议删除或标注出处")
    if pending > 0:
        report.append("- 📋 待核验内容请手动搜索确认")
    if verified > 0:
        report.append("- ✅ 已验证内容可信度较高，可直接引用")
    
    return "\n".join(report)


# ============== 报告摘要模式（v1.3.1新增）==============

def generate_summary_report(result: DetectionResult) -> str:
    """生成简洁摘要报告"""
    summary = []
    
    # 风险等级
    high_risks = result.statistics.get("高风险", 0)
    if high_risks >= 5:
        risk_icon = "🔴"
        risk_text = "高风险"
    elif high_risks >= 2:
        risk_icon = "🟡"
        risk_text = "中风险"
    else:
        risk_icon = "🟢"
        risk_text = "低风险"
    
    summary.append(f"{risk_icon} **{risk_text}内容** ({result.text_length}字，{result.text_type}文本)")
    summary.append("")
    
    # 关键问题（最多3条）
    issues = []
    
    # 伪科学
    if result.pseudoscience_detected:
        issues.append(f"❌ 伪科学表述：{len(result.pseudoscience_detected)}条")
    
    # 科学词汇滥用
    pseudoscience_vocab = []
    for risk_level, vocabs in result.scientific_vocab.items():
        for v in vocabs:
            if not v.is_correct_context:
                pseudoscience_vocab.append(v.vocabulary)
    if pseudoscience_vocab:
        unique_vocab = list(set(pseudoscience_vocab))[:3]
        issues.append(f"⚠️ 科学词汇滥用：{', '.join(unique_vocab)}")
    
    # 专业领域问题
    for domain, vocabs in result.professional_vocab.items():
        high_risk_vocabs = [v for v in vocabs if v.risk_level in ["极高风险", "高风险"]]
        if high_risk_vocabs:
            issues.append(f"⚠️ {domain}领域问题：{high_risk_vocabs[0].vocabulary}")
    
    # 数据问题
    data_risks = [r for r in result.risk_items if r.type == "数据"]
    if data_risks:
        issues.append(f"📊 数据待核实：{len(data_risks)}处")
    
    # 范围问题
    scope_risks = [r for r in result.risk_items if r.type == "范围"]
    if scope_risks:
        issues.append(f"📍 范围待核实：{len(scope_risks)}处")
    
    if issues:
        summary.append("**关键问题**：")
        for issue in issues[:5]:
            summary.append(f"- {issue}")
    else:
        summary.append("**关键问题**：无明显风险 ✅")
    
    summary.append("")
    
    # 行动建议（简版）
    if high_risks >= 3:
        summary.append("**建议**：优先核实高风险项，谨慎采用")
    elif high_risks >= 1:
        summary.append("**建议**：核实标注内容后使用")
    else:
        summary.append("**建议**：可正常使用，注意标注出处")
    
    return "\n".join(summary)


# ============== 命令行入口 ==============

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    enable_verify = "--verify" in sys.argv
    enable_summary = "--summary" in sys.argv or "-s" in sys.argv
    
    if enable_verify:
        sys.argv.remove("--verify")
    if enable_summary:
        if "--summary" in sys.argv:
            sys.argv.remove("--summary")
        if "-s" in sys.argv:
            sys.argv.remove("-s")
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print("请输入要检测的文本（输入完成后按 Ctrl+D 结束）：")
        text = sys.stdin.read()
    
    vocab_db = VocabularyDB()
    result = analyze_text(text, vocab_db)
    
    # 根据模式输出报告
    if enable_summary:
        report = generate_summary_report(result)
    else:
        report = generate_report(result)
    
    print(report)
    
    # 如果启用核验模式，进行出处核验
    if enable_verify:
        print("\n" + "="*60)
        print("出处核验中...")
        print("="*60 + "\n")
        
        verify_results = verify_content(text)
        verify_report = generate_verification_report(verify_results)
        print(verify_report)
        
        print("\n" + "-"*60)
        print("💡 提示：如需使用自动搜索核验，请提供搜索API函数")
        print("   示例：verify_content(text, search_api_func=your_search_function)")
        print("\n📖 使用帮助：")
        print("   python hallucination_detector.py input.txt        # 完整报告")
        print("   python hallucination_detector.py -s input.txt     # 摘要报告")
        print("   python hallucination_detector.py --verify input.txt  # 带出处核验")
