#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI内容说谎检测器 - 多角色风格版本 v1.0.0
功能: 以多种侦探风格检测AI内容中的谎言、伪科学和虚假宣传
支持角色：狄仁杰、包青天、柯南、福尔摩斯、秦风/唐人风格
复用AI内容幻觉检测器的核心检测逻辑
"""

import re
import json
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ============== 配置 ==============

# 词汇库文件路径（复用现有词库）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
HALLUCINATION_SKILL_DIR = os.path.join(os.path.dirname(SKILL_DIR), "skill-ai-hallucination-detector")
VOCABULARY_DB_PATH = os.path.join(HALLUCINATION_SKILL_DIR, "data", "vocabulary_db.json")

# ============== 角色模板定义 ==============

CHARACTER_TEMPLATES = {
    "direnjie": {
        "name": "狄仁杰",
        "era": "唐朝",
        "role": "神探",
        "opening": "元芳，此事必有蹊跷...",
        "analysis_intro": "本官细查此文案，发现以下疑点：",
        "finding_prefix": "其",
        "finding_suffix": "、",
        "conclusion_header": "【断案结论】",
        "conclusion_format": "经本官审理，此文案疑点共计 **{count}** 处。\n最高风险等级：**{risk_level}**\n本案判定：{emoji} **{verdict}**",
        "closing": "元芳，你怎么看？",
        "style_keywords": ["本官", "据查", "典籍", "查阅", "荒谬", "蹊跷", "断案"],
        "risk_verdicts": {
            "极高风险": ("🚨", "欺诈性内容", "此文案疑点重重，虚假成分居多，切勿轻信！"),
            "高风险": ("🚨", "存在欺诈嫌疑", "此文案漏洞百出，真实性存疑，当谨慎对待！"),
            "中风险": ("⚠️", "存在虚假成分", "此文案部分内容难以核实，务必多方求证！"),
            "低风险": ("✅", "基本可信", "此文案暂无明显破绽，但亦需独立核实。"),
            "待确认": ("❓", "尚需考证", "此文案部分内容尚待核实，不可妄下定论。"),
        }
    },
    
    "baoqingtian": {
        "name": "包青天",
        "era": "宋朝",
        "role": "名臣",
        "opening": "王朝马汉，开堂审案！",
        "analysis_intro": "堂下之人听着，本府现已查明此事疑点：",
        "finding_prefix": "一则",
        "finding_suffix": "，",
        "conclusion_header": "【审判结果】",
        "conclusion_format": "本府现已查明，此文案疑点共计 **{count}** 条。\n最高风险等级：**{risk_level}**\n本府判决：{emoji} **{verdict}**",
        "closing": "退堂！",
        "style_keywords": ["本府", "堂下", "判决", "查明", "审案", "开堂", "王朝马汉"],
        "risk_verdicts": {
            "极高风险": ("🔴", "欺君之罪", "此乃欺世盗名之大罪！本府定当严惩不贷！"),
            "高风险": ("🔴", "欺民之罪", "此乃欺骗百姓之举！本府绝不姑息！"),
            "中风险": ("🟡", "存疑待查", "此案疑点重重，本府需进一步查证！"),
            "低风险": ("🟢", "清白", "经本府核实，暂无违法之处。"),
            "待确认": ("❓", "待查", "此案尚需进一步调查。"),
        }
    },
    
    "conan": {
        "name": "柯南",
        "era": "现代日本",
        "role": "侦探",
        "opening": "真相只有一个！...嗯？这段内容好像有问题...",
        "analysis_intro": "经过我的详细调查，发现了这些可疑之处：",
        "finding_prefix": "",
        "finding_suffix": "！",
        "conclusion_header": "【推理结果】",
        "conclusion_format": "经过完美推理，此内容存在 **{count}** 处可疑点！\n危险等级：**{risk_level}**\n我的判断：{emoji} **{verdict}**",
        "closing": "哎嘿嘿～真相大白了！（小声）",
        "style_keywords": ["真相", "推理", "调查", "完美", "可疑", "哎嘿嘿"],
        "risk_verdicts": {
            "极高风险": ("💀", "危险内容", "这简直是胡说八道！完全没有科学依据！"),
            "高风险": ("⚠️", "可疑内容", "这里有问题！逻辑完全不通！"),
            "中风险": ("❓", "存疑内容", "嗯...有些地方说不通，需要再想想。"),
            "低风险": ("✅", "基本正常", "暂时没发现大问题，但还是要注意核实哦～"),
            "待确认": ("❓", "待确认", "这个还需要更多证据来证明。"),
        }
    },
    
    "holmes": {
        "name": "福尔摩斯",
        "era": "维多利亚时代英国",
        "role": "咨询侦探",
        "opening": "Elementary, my dear Watson. Let me examine this... hmm, most peculiar.",
        "analysis_intro": "我亲爱的主人，经过我的观察与分析，发现了以下问题：",
        "finding_prefix": "",
        "finding_suffix": ".",
        "conclusion_header": "【CONCLUSION】",
        "conclusion_format": "My deduction reveals **{count}** suspicious elements.\nRisk Level: **{risk_level}**\nMy verdict: {emoji} **{verdict}**",
        "closing": "The game, as they say, is afoot.",
        "style_keywords": ["Elementary", "Watson", "deduction", "observe", "peculiar", "suspicious"],
        "risk_verdicts": {
            "极高风险": ("☠️", "Manifestly False", "This is utter nonsense! A complete fabrication!"),
            "高风险": ("⚠️", "Highly Suspicious", "Most irregular. This simply will not do."),
            "中风险": ("❓", "Questionable", "Hmm, this requires further investigation."),
            "低风险": ("✅", "Plausible", "Acceptable, though one should remain vigilant."),
            "待确认": ("❓", "Pending Verification", "More evidence is required before judgment."),
        }
    },
    
    "qinfeng": {
        "name": "秦风",
        "era": "现代",
        "role": "天才侦探",
        "opening": "这案子有点意思...等等，这内容好像不太对劲？",
        "analysis_intro": "我发现了 {count} 个疑点，让我用记忆宫殿捋一捋：\n\n{findings}",
        "finding_prefix": "",
        "finding_suffix": "。",
        "conclusion_header": "【真相】",
        "conclusion_format": "经过我的逻辑推理...OK，我搞清楚了！\n\n{emoji} **{verdict}**\n\n（翻白眼）这编得也太不走心了！",
        "closing": "下个案子见！Q.E.D.",
        "style_keywords": ["有点意思", "记忆宫殿", "逻辑", "真相", "Q.E.D.", "我发现了"],
        "mix_english": True,  # 中英文混用
        "risk_verdicts": {
            "极高风险": ("🚨", "Fake到家了", "这内容问题大了去了！logic完全不make sense！鉴定为假！"),
            "高风险": ("⚠️", "很可疑", "emmm...这里逻辑根本不通啊，suspicious！"),
            "中风险": ("❓", "存疑", "嗯...有些地方我memory palace过不去，need more evidence。"),
            "低风险": ("✅", "基本OK", "还行吧，logic基本pass，没有big problem。"),
            "待确认": ("❓", "待挖", "这个case还需要挖一下，not sure yet。"),
        }
    }
}

# 默认角色
DEFAULT_CHARACTER = "direnjie"

# ============== 科学词汇库（复用） ==============

SCIENTIFIC_VOCABULARY = {
    "极高风险": {
        "量子": {"正确语境": ["量子计算", "量子通信", "量子力学"], "伪科学场景": ["量子养生", "量子水", "量子医学", "量子能量", "量子共振"]},
        "干细胞": {"正确语境": ["再生医学", "临床治疗"], "伪科学场景": ["干细胞美容", "干细胞保健品", "干细胞养生", "干细胞面膜"]},
        "DNA": {"正确语境": ["遗传学", "基因检测"], "伪科学场景": ["DNA修复", "DNA激活", "DNA美容", "DNA护肤"]},
        "基因": {"正确语境": ["基因工程", "遗传学"], "伪科学场景": ["基因修复", "基因激活", "基因养生", "基因美容", "基因调控"]},
        "石墨烯": {"正确语境": ["材料科学", "电子器件"], "伪科学场景": ["石墨烯内衣", "石墨烯床垫", "石墨烯保健", "石墨烯养生", "石墨烯袜"]},
        "同位素": {"正确语境": ["核医学", "核化学"], "伪科学场景": ["同位素养生", "同位素能量", "同位素保健"]},
        "辐射": {"正确语境": ["核物理", "医学影像"], "伪科学场景": ["辐射调理", "辐射养生", "辐射能量", "辐射保健"]},
    },
    "高风险": {
        "原子": {"正确语境": ["原子物理", "原子能"], "伪科学场景": ["原子能量", "原子养生", "原子保健"]},
        "粒子": {"正确语境": ["粒子物理", "高能物理"], "伪科学场景": ["粒子修复", "粒子能量", "粒子养生"]},
        "纳米": {"正确语境": ["纳米技术", "材料科学"], "伪科学场景": ["纳米养生", "纳米美容", "纳米保健", "纳米护肤", "纳米面膜"]},
        "细胞": {"正确语境": ["细胞生物学", "医学"], "伪科学场景": ["细胞再生", "细胞激活", "细胞养生", "细胞修复"]},
        "免疫": {"正确语境": ["免疫学", "医学"], "伪科学场景": ["免疫激活", "免疫调理", "免疫养生", "免疫保健"]},
        "靶向": {"正确语境": ["靶向治疗", "医学"], "伪科学场景": ["靶向养生", "靶向修复", "靶向保健"]},
        "磁场": {"正确语境": ["电磁学", "地球物理"], "伪科学场景": ["磁场调理", "磁场疗愈", "磁场养生", "磁场保健"]},
        "端粒": {"正确语境": ["分子生物学"], "伪科学场景": ["端粒延长", "端粒激活", "端粒修复", "端粒逆龄"]},
        "肽": {"正确语境": ["生物化学", "医学"], "伪科学场景": ["活性肽", "肽能量", "肽养生", "肽美容"]},
    },
    "中风险": {
        "模型": {"正确语境": ["机器学习", "AI"], "伪科学场景": ["万能模型", "神奇模型"]},
        "算法": {"正确语境": ["计算机科学"], "伪科学场景": ["算法养生", "算法调理"]},
        "神经网络": {"正确语境": ["深度学习", "AI"], "伪科学场景": ["神经网络激活", "神经网络修复"]},
        "酶": {"正确语境": ["生物化学", "医学"], "伪科学场景": ["酶激活", "酶能量", "酶修复"]},
        "分子": {"正确语境": ["化学", "分子生物学"], "伪科学场景": ["分子能量", "分子调理", "分子修复"]},
    },
}

# 专业领域极高风险词汇
PROFESSIONAL_HIGH_RISK = {
    "医疗": ["根治", "百分百治愈", "包治", "无副作用", "祖传秘方", "神医", "灵丹妙药", "药到病除", "彻底治愈", "永不复发"],
    "金融": ["内幕消息", "稳赚不赔", "保本保息", "年化收益100%", "日赚十万", "一本万利"],
    "教育": ["保过", "包录取", "内部名额", "真题泄露", "必考点", "押题率100%"],
    "法律": ["包赢", "必胜诉", "关系硬", "特殊渠道", "有后台", "能摆平"],
}

# 伪科学产品关键词组合
PSEUDOSCIENCE_PATTERNS = [
    (r"量子.{0,8}(水|杯|袜|衣|垫|枕|手环|项链|能量|养生|技术|产品)", "极高风险"),
    (r"纳米.{0,8}(内衣|床垫|袜子|保健|养生|美容|技术|产品|面膜|精华)", "高风险"),
    (r"干细胞.{0,8}(美容|保健品|养生|护肤|面膜|精华液)", "极高风险"),
    (r"DNA.{0,8}(修复|激活|美容|护肤|霜|护手)", "极高风险"),
    (r"基因.{0,8}(修复|激活|养生|美容|调控|密码)", "极高风险"),
    (r"石墨烯.{0,8}(内衣|床垫|保健|养生|袜)", "极高风险"),
    (r"能量.{0,8}(场|波|共振|调理|技术)", "高风险"),
    (r"磁.{0,8}(场.{0,5}调理|疗愈|养生|技术)", "高风险"),
    (r"端粒.{0,8}(延长|激活|逆转|修复)", "高风险"),
    (r"(7|七)天.{0,8}(根治|治愈|痊愈|治好|告别)", "极高风险"),
    (r"(一个月|30天|一个月).{0,8}(彻底|完全|彻底地).{0,8}(治愈|治好|根治)", "极高风险"),
    (r"永不复发", "极高风险"),
    (r"100%有效", "极高风险"),
    (r"(彻底|完全|100%).{0,5}(治愈|根治|告别|摆脱)", "极高风险"),
    (r"(祖传|秘方|神医|灵丹).{0,10}(治病|治疗|治愈|调理)", "极高风险"),
]

# 绝对化表述
ABSOLUTE_EXPRESSIONS = ["一定", "必定", "肯定", "绝对", "必然", "所有", "全部", "完全", "彻底", "根本", "永远", "保证", "承诺", "必须", "务必"]

# ============== 数据结构 ==============

@dataclass
class LiarItem:
    """说谎项"""
    type: str
    content: str
    risk_level: str
    interpretation: str


@dataclass
class LiarDetectionResult:
    """说谎检测结果"""
    original_text: str = ""
    text_length: int = 0
    character: str = DEFAULT_CHARACTER
    liar_items: List[LiarItem] = field(default_factory=list)
    highest_risk_level: str = "低风险"
    report: str = ""


# ============== 核心检测函数 ==============

def detect_text_type(text: str) -> str:
    """判断文本类型"""
    if len(text) < 100:
        return "short"
    elif len(text) < 500:
        return "medium"
    else:
        return "long"


def detect_scientific_vocabulary(text: str) -> Tuple[List[LiarItem], str]:
    """检测科学词汇滥用"""
    detected_items = []
    highest_risk = "低风险"
    
    for risk_level, vocab_dict in SCIENTIFIC_VOCABULARY.items():
        for vocab, context_info in vocab_dict.items():
            if vocab in text:
                pattern = rf".{{0,20}}{vocab}.{{0,30}}"
                matches = re.findall(pattern, text)
                
                for match in matches:
                    pseudoscience_contexts = context_info.get("伪科学场景", [])
                    is_pseudoscience = any(ctx in match for ctx in pseudoscience_contexts)
                    
                    if is_pseudoscience:
                        interpretation = generate_interpretation(vocab, match, risk_level)
                        detected_items.append(LiarItem(
                            type="伪科学词汇",
                            content=f"「{vocab}」",
                            risk_level=risk_level,
                            interpretation=interpretation
                        ))
                        
                        if risk_level == "极高风险":
                            highest_risk = "极高风险"
                        elif risk_level == "高风险" and highest_risk not in ["极高风险"]:
                            highest_risk = "高风险"
    
    return detected_items, highest_risk


def detect_professional_vocabulary(text: str) -> Tuple[List[LiarItem], str]:
    """检测专业领域高风险词汇"""
    detected_items = []
    highest_risk = "低风险"
    
    for domain, vocabs in PROFESSIONAL_HIGH_RISK.items():
        for vocab in vocabs:
            if vocab in text:
                pattern = rf".{{0,15}}{vocab}.{{0,15}}"
                matches = re.findall(pattern, text)
                
                for match in matches:
                    interpretation = f"「{match.strip()}」——此乃{domain}界之大忌，天下并无此等保证之法！"
                    
                    detected_items.append(LiarItem(
                        type=f"{domain}类绝对化表述",
                        content=match.strip(),
                        risk_level="极高风险",
                        interpretation=interpretation
                    ))
                    highest_risk = "极高风险"
    
    return detected_items, highest_risk


def detect_pseudoscience_patterns(text: str) -> Tuple[List[LiarItem], str]:
    """检测伪科学产品组合"""
    detected_items = []
    highest_risk = "低风险"
    
    for pattern, risk in PSEUDOSCIENCE_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            if risk == "极高风险":
                interpretation = f"「{match}」——此乃伪科学惯用伎俩，查阅典籍无据可考，恐是欺世盗名！"
            else:
                interpretation = f"「{match}」——此类说法荒谬至极，本官从未见典籍有载！"
            
            detected_items.append(LiarItem(
                type="伪科学产品组合",
                content=match,
                risk_level=risk,
                interpretation=interpretation
            ))
            
            if risk == "极高风险":
                highest_risk = "极高风险"
            elif risk == "高风险" and highest_risk not in ["极高风险"]:
                highest_risk = "高风险"
    
    return detected_items, highest_risk


def detect_absolute_expressions(text: str) -> Tuple[List[LiarItem], str]:
    """检测绝对化表述"""
    detected_items = []
    highest_risk = "低风险"
    
    for expr in ABSOLUTE_EXPRESSIONS:
        if expr in text:
            pattern = rf".{{0,10}}{expr}.{{0,15}}"
            matches = re.findall(pattern, text)
            
            for match in matches:
                interpretation = f"「{expr}」——此乃绝对化表述，天下岂有此等保证？"
                
                detected_items.append(LiarItem(
                    type="绝对化表述",
                    content=match.strip(),
                    risk_level="高风险",
                    interpretation=interpretation
                ))
                
                if highest_risk not in ["极高风险"]:
                    highest_risk = "高风险"
    
    return detected_items, highest_risk


def detect_suspicious_data(text: str) -> Tuple[List[LiarItem], str]:
    """检测可疑数据"""
    detected_items = []
    highest_risk = "低风险"
    
    # 检测超大数值
    huge_numbers = re.findall(r"(\d+(?:\.\d+)?)\s*(万亿|亿|万)", text)
    for num, unit in huge_numbers:
        num_value = float(num)
        if unit in ["万亿", "亿"]:
            if "市场规模" in text or "市场" in text or "规模" in text:
                if unit == "万亿" and num_value > 100:
                    interpretation = f"「{num}{unit}」——此数之巨，令人咋舌！市场规模岂能超越GDP数倍？数据浮夸，难辨真伪！"
                    detected_items.append(LiarItem(
                        type="数据可疑",
                        content=f"{num}{unit}",
                        risk_level="高风险",
                        interpretation=interpretation
                    ))
                    if highest_risk not in ["极高风险"]:
                        highest_risk = "高风险"
    
    # 检测百分比异常
    percentages = re.findall(r"(\d+(?:\.\d+)?)\s*[%％]", text)
    for pct in percentages:
        pct_value = float(pct)
        if pct_value > 100:
            interpretation = f"「{pct}%」——百分比岂能超过百分之百？此数据荒谬至极！"
            detected_items.append(LiarItem(
                type="数据异常",
                content=f"{pct}%",
                risk_level="高风险",
                interpretation=interpretation
            ))
            if highest_risk not in ["极高风险"]:
                highest_risk = "高风险"
    
    return detected_items, highest_risk


def generate_interpretation(vocab: str, context: str, risk_level: str) -> str:
    """生成解读"""
    
    interpretations = {
        "量子": f"「{context}」——量子乃物理学之精深学问，岂能与日常之物相提并论？此乃科技术语滥用！",
        "干细胞": f"「{context}」——干细胞乃医学前沿技术，岂可混入寻常产品？此乃伪科学营销！",
        "DNA": f"「{context}」——DNA乃遗传学之根基，岂是护肤品能修复之物？此乃欺骗无知！",
        "基因": f"「{context}」——基因乃生命密码，岂可随意修复激活？此乃伪科学无疑！",
        "纳米": f"「{context}」——纳米乃材料科学之术语，日常生活用品岂需纳米科技？此乃故弄玄虚！",
        "磁场": f"「{context}」——磁场乃物理学概念，岂能随意调理人体？此乃伪科学骗局！",
        "石墨烯": f"「{context}」——石墨烯乃高端材料，岂会用于内衣床垫？此乃虚假宣传！",
        "辐射": f"「{context}」——辐射岂能养生？此乃颠倒黑白！",
        "端粒": f"「{context}」——端粒乃细胞衰老研究课题，岂是护肤品能影响？此乃欺骗！",
    }
    
    if any(keyword in context for keyword in ["养生", "美容", "保健", "修复", "激活", "调理", "疗愈", "护肤", "面膜", "精华", "内衣", "床垫", "袜", "杯", "水", "能量", "共振", "密码"]):
        return f"「{context}」——此类说法，查阅典籍从无记载，恐是欺世盗名！"
    
    return interpretations.get(vocab, f"「{context}」——此乃科技术语乱用，不可轻信！")


def generate_report(result: LiarDetectionResult) -> str:
    """生成对应角色风格的报告"""
    
    template = CHARACTER_TEMPLATES.get(result.character, CHARACTER_TEMPLATES[DEFAULT_CHARACTER])
    
    lines = []
    
    # 开场白
    if result.character == "holmes":
        lines.append(f"_{template['opening']}_")
    else:
        lines.append(f"**【{template['name']}断案】**" if result.character == "direnjie" else f"**【{template['name']}模式】**")
        lines.append("")
        lines.append(f"*{template['opening']}*")
    lines.append("")
    
    # 分析过程
    if result.liar_items:
        if result.character == "qinfeng":
            # 秦风特殊格式
            findings_text = []
            for i, item in enumerate(result.liar_items[:5], 1):  # 最多5个
                ordinal_map = {"1": "第一", "2": "第二", "3": "第三", "4": "第四", "5": "第五"}
                findings_text.append(f"{ordinal_map.get(str(i), str(i))}个：「{item.content}」——{item.interpretation}")
            
            analysis = template['analysis_intro'].format(
                count=len(result.liar_items),
                findings="\n".join(findings_text)
            )
            lines.append(analysis)
        else:
            lines.append(f"_{template['analysis_intro']}_")
            lines.append("")
            
            for i, item in enumerate(result.liar_items, 1):
                if result.character == "direnjie":
                    lines.append(f"**{template['finding_prefix']}{i}{template['finding_suffix']}** {item.interpretation}")
                elif result.character == "baoqingtian":
                    lines.append(f"**{template['finding_prefix']}{i}{template['finding_suffix']}** {item.interpretation}")
                elif result.character == "conan":
                    lines.append(f"**疑点{i}：** {item.interpretation}")
                elif result.character == "holmes":
                    lines.append(f"**{i}.** {item.interpretation}")
                lines.append("")
    else:
        if result.character == "qinfeng":
            lines.append("嗯...我反复看了好几遍，好像没发现什么问题？")
            lines.append("但是！我还是建议保持警惕，independently verify一下。")
        elif result.character == "conan":
            lines.append("嗯...暂时没发现明显可疑的地方。")
            lines.append("但是，真相可能藏在更深的地方...要保持警惕哦！")
        elif result.character == "holmes":
            lines.append("Hmm, I observe nothing immediately suspicious.")
            lines.append("However, one should always verify independently.")
        elif result.character == "baoqingtian":
            lines.append("本府明察秋毫，暂未发现欺瞒之处...")
            lines.append("然，百姓仍需谨慎行事，不可大意！")
        else:
            lines.append("本官细细查探，未见明显破绽...")
            lines.append("然，为民者当谨慎行事，不可大意！")
        lines.append("")
    
    # 断案结论
    emoji, verdict = template['risk_verdicts'].get(result.highest_risk_level, template['risk_verdicts']['低风险'])[0:2]
    
    lines.append(f"**{template['conclusion_header']}**")
    
    conclusion_format = template['conclusion_format']
    if "{count}" in conclusion_format:
        conclusion_text = conclusion_format.format(
            count=len(result.liar_items),
            risk_level=result.highest_risk_level,
            emoji=emoji,
            verdict=verdict
        )
    else:
        conclusion_text = f"{emoji} **{verdict}**"
    
    for line in conclusion_text.split("\n"):
        lines.append(line)
    lines.append("")
    
    # 结尾语
    if result.character == "holmes":
        lines.append(f"_{template['closing']}_")
    else:
        lines.append(f"_{template['closing']}_")
    
    return "\n".join(lines)


def detect_liar(text: str, character: str = DEFAULT_CHARACTER) -> LiarDetectionResult:
    """
    检测文本中的谎言/伪科学内容
    
    Args:
        text: 待检测的文本
        character: 检测角色风格 (direnjie/baoqingtian/conan/holmes/qinfeng)
        
    Returns:
        LiarDetectionResult: 包含角色风格报告的检测结果
    """
    # 验证角色
    if character not in CHARACTER_TEMPLATES:
        character = DEFAULT_CHARACTER
    
    result = LiarDetectionResult()
    result.original_text = text
    result.text_length = len(text)
    result.character = character
    
    # 执行各项检测
    all_items = []
    highest_risk = "低风险"
    
    # 1. 检测伪科学词汇
    vocab_items, vocab_risk = detect_scientific_vocabulary(text)
    all_items.extend(vocab_items)
    if vocab_risk == "极高风险":
        highest_risk = "极高风险"
    elif vocab_risk == "高风险" and highest_risk != "极高风险":
        highest_risk = "高风险"
    
    # 2. 检测专业领域高风险词汇
    prof_items, prof_risk = detect_professional_vocabulary(text)
    all_items.extend(prof_items)
    if prof_risk == "极高风险":
        highest_risk = "极高风险"
    elif prof_risk == "高风险" and highest_risk != "极高风险":
        highest_risk = "高风险"
    
    # 3. 检测伪科学产品组合
    pattern_items, pattern_risk = detect_pseudoscience_patterns(text)
    all_items.extend(pattern_items)
    if pattern_risk == "极高风险":
        highest_risk = "极高风险"
    elif pattern_risk == "高风险" and highest_risk != "极高风险":
        highest_risk = "高风险"
    
    # 4. 检测绝对化表述
    abs_items, abs_risk = detect_absolute_expressions(text)
    all_items.extend(abs_items)
    if abs_risk == "极高风险":
        highest_risk = "极高风险"
    elif abs_risk == "高风险" and highest_risk != "极高风险":
        highest_risk = "高风险"
    
    # 5. 检测可疑数据
    data_items, data_risk = detect_suspicious_data(text)
    all_items.extend(data_items)
    if data_risk == "极高风险":
        highest_risk = "极高风险"
    elif data_risk == "高风险" and highest_risk != "极高风险":
        highest_risk = "高风险"
    
    # 去重
    seen = set()
    unique_items = []
    for item in all_items:
        if item.content not in seen:
            seen.add(item.content)
            unique_items.append(item)
    
    # 排序
    risk_order = {"极高风险": 0, "高风险": 1, "中风险": 2, "低风险": 3, "待确认": 4}
    unique_items.sort(key=lambda x: risk_order.get(x.risk_level, 4))
    
    result.liar_items = unique_items
    result.highest_risk_level = highest_risk
    result.report = generate_report(result)
    
    return result


def get_available_characters() -> List[Dict]:
    """获取可用角色列表"""
    return [
        {
            "id": char_id,
            "name": template["name"],
            "era": template["era"],
            "role": template["role"],
            "example_opening": template["opening"]
        }
        for char_id, template in CHARACTER_TEMPLATES.items()
    ]


def main():
    """命令行测试"""
    import sys
    
    # 获取角色参数
    character = DEFAULT_CHARACTER
    test_text = ""
    
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args[0].startswith("--character="):
            character = args[0].split("=")[1]
            test_text = " ".join(args[1:])
        else:
            test_text = " ".join(args)
    
    if not test_text:
        test_text = "量子共振技术，7天根治糖尿病，让你彻底摆脱药物依赖！"
    
    print(f"【角色】: {CHARACTER_TEMPLATES.get(character, CHARACTER_TEMPLATES[DEFAULT_CHARACTER])['name']}")
    print(f"【检测文本】: {test_text}")
    print("-" * 60)
    
    result = detect_liar(test_text, character)
    print(result.report)
    
    print("\n" + "=" * 60)
    print("【可用角色】:")
    for char in get_available_characters():
        print(f"  - {char['id']}: {char['name']}（{char['era']}）")


if __name__ == "__main__":
    main()
