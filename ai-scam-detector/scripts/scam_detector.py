#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI营销骗局识别器 - 多角色风格版本 v2.0.0
功能: 以多种侦探风格识别营销文案中的虚假信息、消费陷阱和诈骗套路
支持场景：保健品广告、投资理财骗局、网购商品真假、传销话术识别
支持角色：狄仁杰、包青天、柯南、福尔摩斯、秦风/唐人风格
"""

import re
import json
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ============== 配置 ==============

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
HALLUCINATION_SKILL_DIR = os.path.join(os.path.dirname(SKILL_DIR), "skill-ai-hallucination-detector")
VOCABULARY_DB_PATH = os.path.join(HALLUCINATION_SKILL_DIR, "data", "vocabulary_db.json")

# ============== 新增：骗局模式库 ==============

SCAM_PATTERNS = {
    # 传销/拉人头模式
    "pyramid_scheme": {
        "keywords": ["邀请.*回本", "拉人头", "团队.*分成", "下线.*佣金", "多层次分销", "裂变.*收益"],
        "description": "传销/拉人头模式",
        "risk": "极高风险"
    },
    
    # 投资诈骗
    "investment_fraud": {
        "keywords": ["稳赚不赔", "包赚不亏", "内部消息", "必涨", "月入过万.*不是梦", "躺着赚钱"],
        "description": "投资诈骗话术",
        "risk": "极高风险"
    },
    
    # 价格欺诈
    "price_fraud": {
        "keywords": ["原价.*现价.*[1-9]9", "仅剩.*名额", "限时.*最后", "错过.*后悔", "绝版.*清仓"],
        "description": "价格欺诈套路",
        "risk": "高风险"
    },
    
    # 保健品虚假宣传
    "health_fraud": {
        "keywords": ["根治.*慢性病", "7天.*见效", "永不复发", "无任何副作用", "替代.*药物", "包治百病"],
        "description": "保健品虚假宣传",
        "risk": "极高风险"
    },
    
    # 电商假货
    "fake_product": {
        "keywords": ["专柜验货", "原单.*尾货", "海关扣货", "工厂直销.*[1-9]折", "代购.*白菜价"],
        "description": "疑似假货话术",
        "risk": "高风险"
    }
}

# ============== 举报渠道 ==============

REPORT_CHANNELS = {
    "虚假广告": {"渠道": "市场监督管理局", "电话": "12315"},
    "消费纠纷": {"渠道": "消费者协会", "电话": "12315"},
    "网络诈骗": {"渠道": "公安机关", "电话": "110"},
    "网络违法": {"渠道": "网信办", "电话": "12321"},
    "金融诈骗": {"渠道": "银保监会", "电话": "12378"},
    "证券违法": {"渠道": "证监会", "电话": "12386"},
}

# ============== 维权建议 ==============

RIGHTS_ADVICE = {
    "极高风险": [
        "立即停止交易",
        "保存所有聊天记录和转账凭证",
        "向公安机关报案（110）",
        "如涉及投资理财，向证监会举报（12386）"
    ],
    "高风险": [
        "谨慎购买，要求商家提供完整资质",
        "查看产品防伪码和批号",
        "保留购物凭证和聊天记录",
        "如有纠纷，拨打12315投诉"
    ],
    "中风险": [
        "货比三家，理性消费",
        "核实商家资质和产品信息",
        "注意保留购物凭证"
    ],
    "低风险": [
        "可正常购买，保留购物凭证",
        "收到商品后仔细查验"
    ]
}

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
            "极高风险": ("🚨", "疑似诈骗", "此文案疑点重重，恐是欺世盗名之举，切勿轻信！"),
            "高风险": ("⚠️", "虚假宣传", "此文案漏洞百出，真实性存疑，当谨慎对待！"),
            "中风险": ("🟡", "夸大营销", "此文案部分内容难以核实，务必多方求证！"),
            "低风险": ("✅", "基本可信", "此文案暂无明显破绽，但亦需独立核实。"),
        },
        "advice_intro": "【维权建议】"
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
            "极高风险": ("🚨", "涉嫌诈骗", "此乃欺世盗名之大罪！本府定当严惩不贷！"),
            "高风险": ("⚠️", "虚假宣传", "此乃欺骗百姓之举！本府绝不姑息！"),
            "中风险": ("🟡", "存疑待查", "此案疑点重重，本府需进一步查证！"),
            "低风险": ("✅", "清白", "经本府核实，暂无违法之处。"),
        },
        "advice_intro": "【本府建议】"
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
        "closing": "哎嘿嘿～真相大白了！（推眼镜）",
        "style_keywords": ["真相", "推理", "调查", "完美", "可疑", "哎嘿嘿"],
        "risk_verdicts": {
            "极高风险": ("🚨", "诈骗警报", "这简直是诈骗！完全没有可信度！"),
            "高风险": ("⚠️", "虚假警报", "这里有大问题！千万别信！"),
            "中风险": ("🟡", "存疑警报", "嗯...有些地方说不通，需要再想想。"),
            "低风险": ("✅", "基本正常", "暂时没发现大问题，但还是要注意核实哦～"),
        },
        "advice_intro": "【我的建议】"
    },
    
    "holmes": {
        "name": "福尔摩斯",
        "era": "维多利亚时代英国",
        "role": "咨询侦探",
        "opening": "Elementary, my dear Watson. Let me examine this... hmm, most peculiar.",
        "analysis_intro": "我亲爱的朋友，经过我的观察与分析，发现了以下问题：",
        "finding_prefix": "",
        "finding_suffix": ".",
        "conclusion_header": "【CONCLUSION】",
        "conclusion_format": "My deduction reveals **{count}** suspicious elements.\nRisk Level: **{risk_level}**\nMy verdict: {emoji} **{verdict}**",
        "closing": "The game, as they say, is afoot.",
        "style_keywords": ["deduction", "observation", "elementary", "peculiar", "suspicious"],
        "risk_verdicts": {
            "极高风险": ("🚨", "Manifestly Fraudulent", "This is clearly a scam. Do not engage."),
            "高风险": ("⚠️", "Highly Suspicious", "I detect significant red flags. Exercise extreme caution."),
            "中风险": ("🟡", "Questionable", "Some elements require further investigation."),
            "低风险": ("✅", "Appears Legitimate", "No obvious red flags detected, but verify independently."),
        },
        "advice_intro": "【ADVICE】"
    },
    
    "qinfeng": {
        "name": "秦风",
        "era": "现代中国",
        "role": "天才侦探",
        "opening": "这案子有点意思...等等，这内容好像不太对劲？",
        "analysis_intro": "我发现了X个疑点，让我用记忆宫殿捋一捋：",
        "finding_prefix": "第",
        "finding_suffix": "——",
        "conclusion_header": "【真相】",
        "conclusion_format": "经过我的逻辑推理...OK，我搞清楚了！\n疑点共计 **{count}** 处\n风险等级：**{risk_level}**\n我的判断：{emoji} **{verdict}**",
        "closing": "下个案子见！Q.E.D.",
        "style_keywords": ["记忆宫殿", "逻辑推理", "emmm", "suspicious", "make sense", "Q.E.D."],
        "risk_verdicts": {
            "极高风险": ("🚨", "Fake到家了", "这编得也太不走心了！纯属诈骗！"),
            "高风险": ("⚠️", "有问题", "逻辑完全make sense？我看悬！"),
            "中风险": ("🟡", "存疑", "emmm...有些地方说不通，需要再看看。"),
            "低风险": ("✅", "基本OK", "暂时没发现大问题，但别忘了核实。"),
        },
        "advice_intro": "【我的建议】"
    }
}

# ============== 科学词汇库（复用） ==============

def load_vocabulary_db() -> Dict:
    """加载词汇库"""
    try:
        if os.path.exists(VOCABULARY_DB_PATH):
            with open(VOCABULARY_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    
    # 默认词汇库
    return {
        "极高风险词汇": ["量子养生", "干细胞美容", "DNA修复", "基因编辑", "纳米保健"],
        "高风险词汇": ["根治", "100%有效", "永不复发", "包治百病", "替代药物"],
        "中风险词汇": ["显著改善", "临床试验证明", "专家推荐", "专利技术"]
    }

# ============== 检测核心类 ==============

@dataclass
class DetectionResult:
    """检测结果"""
    character: str
    findings: List[str]
    risk_level: str
    verdict: str
    scam_types: List[str]
    rights_advice: List[str]
    report_channels: Dict[str, Dict]

class ScamDetector:
    """营销骗局识别器"""
    
    def __init__(self, character: str = "direnjie"):
        self.character = character
        self.template = CHARACTER_TEMPLATES.get(character, CHARACTER_TEMPLATES["direnjie"])
        self.vocabulary_db = load_vocabulary_db()
    
    def detect(self, content: str) -> DetectionResult:
        """检测内容"""
        findings = []
        scam_types = []
        
        # 1. 检测科学词汇滥用
        vocab_findings = self._detect_vocabulary_abuse(content)
        findings.extend(vocab_findings)
        
        # 2. 检测骗局模式
        scam_findings, detected_types = self._detect_scam_patterns(content)
        findings.extend(scam_findings)
        scam_types.extend(detected_types)
        
        # 3. 检测绝对化表述
        absolute_findings = self._detect_absolute_statements(content)
        findings.extend(absolute_findings)
        
        # 4. 检测数据可疑性
        data_findings = self._detect_suspicious_data(content)
        findings.extend(data_findings)
        
        # 计算风险等级
        risk_level = self._calculate_risk_level(findings, scam_types)
        
        # 获取维权建议
        rights_advice = RIGHTS_ADVICE.get(risk_level, [])
        
        # 获取举报渠道
        report_channels = self._get_report_channels(scam_types)
        
        return DetectionResult(
            character=self.character,
            findings=findings,
            risk_level=risk_level,
            verdict=self.template["risk_verdicts"].get(risk_level, ("❓", "待确认", "需进一步核实"))[1],
            scam_types=scam_types,
            rights_advice=rights_advice,
            report_channels=report_channels
        )
    
    def _detect_vocabulary_abuse(self, content: str) -> List[str]:
        """检测科学词汇滥用"""
        findings = []
        
        # 极高风险词汇
        for term in self.vocabulary_db.get("极高风险词汇", []):
            if term in content:
                findings.append(f"「{term}」——此乃科技术语滥用，涉嫌伪科学宣传！")
        
        # 高风险词汇
        for term in self.vocabulary_db.get("高风险词汇", []):
            if term in content:
                findings.append(f"「{term}」——此乃绝对化表述，违反广告法！")
        
        return findings
    
    def _detect_scam_patterns(self, content: str) -> Tuple[List[str], List[str]]:
        """检测骗局模式"""
        findings = []
        detected_types = []
        
        for pattern_name, pattern_info in SCAM_PATTERNS.items():
            for keyword in pattern_info["keywords"]:
                if re.search(keyword, content):
                    findings.append(f"「{keyword}」——{pattern_info['description']}！")
                    detected_types.append(pattern_info["description"])
                    break
        
        return findings, detected_types
    
    def _detect_absolute_statements(self, content: str) -> List[str]:
        """检测绝对化表述"""
        findings = []
        absolute_patterns = [
            (r"根治", "根治——天下岂有此等神物？"),
            (r"100%.*有效", "100%有效——此乃绝对化承诺，不可信！"),
            (r"永不复发", "永不复发——医学上不可能的承诺！"),
            (r"无任何副作用", "无任何副作用——此乃虚假宣传，任何药物都有副作用！"),
            (r"包治百病", "包治百病——天下岂有此等神药？"),
        ]
        
        for pattern, desc in absolute_patterns:
            if re.search(pattern, content):
                findings.append(f"「{pattern}」——{desc}")
        
        return findings
    
    def _detect_suspicious_data(self, content: str) -> List[str]:
        """检测可疑数据"""
        findings = []
        
        # 检测过于精确的数据
        precise_numbers = re.findall(r'(\d+\.?\d*%)', content)
        for num in precise_numbers:
            if float(num.rstrip('%')) > 95:
                findings.append(f"「{num}」——数据过于完美，可信度存疑！")
        
        # 检测夸大的时间承诺
        time_claims = re.findall(r'(\d+)天.*(?:见效|治愈|瘦身|美白)', content)
        for days in time_claims:
            if int(days) < 30:
                findings.append(f"「{days}天见效」——短期内见效的承诺，涉嫌虚假宣传！")
        
        return findings
    
    def _calculate_risk_level(self, findings: List[str], scam_types: List[str]) -> str:
        """计算风险等级"""
        # 如果检测到传销或投资诈骗模式
        if any("传销" in t or "投资诈骗" in t for t in scam_types):
            return "极高风险"
        
        # 如果检测到保健品或假货模式
        if any("保健品" in t or "假货" in t for t in scam_types):
            return "高风险"
        
        # 根据疑点数量判断
        if len(findings) >= 4:
            return "极高风险"
        elif len(findings) >= 2:
            return "高风险"
        elif len(findings) >= 1:
            return "中风险"
        else:
            return "低风险"
    
    def _get_report_channels(self, scam_types: List[str]) -> Dict[str, Dict]:
        """获取举报渠道"""
        channels = {}
        
        for scam_type in scam_types:
            if "传销" in scam_type or "投资诈骗" in scam_type:
                channels["公安机关"] = {"电话": "110"}
                channels["证监会"] = {"电话": "12386"}
            elif "保健品" in scam_type:
                channels["市监局"] = {"电话": "12315"}
            elif "假货" in scam_type:
                channels["市监局"] = {"电话": "12315"}
            elif "价格欺诈" in scam_type:
                channels["消协"] = {"电话": "12315"}
        
        return channels or {"市监局": {"电话": "12315"}}
    
    def format_output(self, result: DetectionResult) -> str:
        """格式化输出"""
        template = self.template
        
        # 开场白
        output = f"【{template['name']}模式】\n\n{template['opening']}\n\n"
        
        # 分析部分
        output += f"{template['analysis_intro']}\n\n"
        
        for i, finding in enumerate(result.findings, 1):
            output += f"{template['finding_prefix']}{i}、{finding}\n"
        
        # 结论部分
        output += f"\n{template['conclusion_header']}\n"
        
        emoji, verdict, _ = template["risk_verdicts"].get(result.risk_level, ("❓", "待确认", ""))
        output += template["conclusion_format"].format(
            count=len(result.findings),
            risk_level=result.risk_level,
            emoji=emoji,
            verdict=verdict
        )
        
        # 维权建议
        if result.rights_advice:
            output += f"\n\n{template.get('advice_intro', '【建议】')}\n"
            for i, advice in enumerate(result.rights_advice, 1):
                output += f"{i}. {advice}\n"
        
        # 举报渠道
        if result.report_channels and result.risk_level in ["极高风险", "高风险"]:
            output += "\n【举报渠道】\n"
            for channel, info in result.report_channels.items():
                output += f"- {channel}：{info['电话']}\n"
        
        # 结束语
        output += f"\n{template['closing']}"
        
        return output


def main():
    """主函数 - 示例用法"""
    # 示例：狄仁杰风格检测
    detector = ScamDetector("direnjie")
    
    test_content = """
    量子共振养生舱，采用NASA航天技术，7天疏通经络，30天调理五脏六腑，根治慢性病
    """
    
    result = detector.detect(test_content)
    output = detector.format_output(result)
    print(output)


if __name__ == "__main__":
    main()
