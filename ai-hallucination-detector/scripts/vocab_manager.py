#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词汇库管理工具
功能：查看、确认、添加、删除词汇
"""

import json
import os
from datetime import datetime

# 路径配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
VOCABULARY_DB_PATH = os.path.join(DATA_DIR, "vocabulary_db.json")
NEW_VOCABULARY_PATH = os.path.join(DATA_DIR, "new_vocabulary_found.json")


def load_json(path):
    """加载JSON文件"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def save_json(path, data):
    """保存JSON文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def show_new_vocabulary():
    """显示待确认的新词汇"""
    new_vocab = load_json(NEW_VOCABULARY_PATH)
    if not new_vocab:
        print("暂无待确认的新词汇")
        return
    
    print("\n" + "="*60)
    print("📋 待确认的新词汇列表")
    print("="*60)
    
    for i, vocab in enumerate(new_vocab, 1):
        print(f"\n【{i}】{vocab['vocabulary']}")
        print(f"   语境：{vocab['context']}")
        print(f"   发现时间：{vocab['found_time']}")
        print(f"   当前风险等级：{vocab['risk_level']}")
        print("-"*60)


def confirm_vocabulary(vocab_index: int, action: str, risk_level: str = None, correct_contexts: list = None, pseudo_contexts: list = None):
    """
    确认词汇
    action: 'add' 添加到词汇库, 'delete' 删除, 'skip' 跳过
    """
    new_vocab = load_json(NEW_VOCABULARY_PATH)
    if not new_vocab or vocab_index < 1 or vocab_index > len(new_vocab):
        print("❌ 无效的词汇索引")
        return False
    
    vocab = new_vocab[vocab_index - 1]
    
    if action == 'delete':
        # 删除误识别的词汇
        new_vocab.pop(vocab_index - 1)
        save_json(NEW_VOCABULARY_PATH, new_vocab)
        print(f"✅ 已删除词汇：「{vocab['vocabulary']}」")
        return True
    
    if action == 'add':
        if not risk_level:
            print("❌ 请指定风险等级（极高风险/高风险/中风险）")
            return False
        
        # 加载词汇库
        vocab_db = load_json(VOCABULARY_DB_PATH)
        
        # 添加到词汇库
        vocab_entry = {
            "正确语境": correct_contexts or [],
            "伪科学场景": pseudo_contexts or []
        }
        
        if risk_level not in vocab_db["scientific"]:
            vocab_db["scientific"][risk_level] = {}
        
        vocab_db["scientific"][risk_level][vocab['vocabulary']] = vocab_entry
        vocab_db["stats"]["new_vocab_added"] = vocab_db["stats"].get("new_vocab_added", 0) + 1
        vocab_db["stats"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # 保存词汇库
        save_json(VOCABULARY_DB_PATH, vocab_db)
        
        # 从待确认列表中移除
        new_vocab.pop(vocab_index - 1)
        save_json(NEW_VOCABULARY_PATH, new_vocab)
        
        print(f"✅ 已添加词汇：「{vocab['vocabulary']}」 → {risk_level}")
        return True
    
    return False


def add_vocabulary_manually(vocabulary: str, risk_level: str, correct_contexts: list, pseudo_contexts: list):
    """手动添加词汇到词汇库"""
    vocab_db = load_json(VOCABULARY_DB_PATH)
    
    vocab_entry = {
        "正确语境": correct_contexts or [],
        "伪科学场景": pseudo_contexts or []
    }
    
    if risk_level not in vocab_db["scientific"]:
        vocab_db["scientific"][risk_level] = {}
    
    vocab_db["scientific"][risk_level][vocabulary] = vocab_entry
    vocab_db["stats"]["new_vocab_added"] = vocab_db["stats"].get("new_vocab_added", 0) + 1
    vocab_db["stats"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    save_json(VOCABULARY_DB_PATH, vocab_db)
    print(f"✅ 已添加词汇：「{vocabulary}」 → {risk_level}")


def show_vocabulary_stats():
    """显示词汇库统计"""
    vocab_db = load_json(VOCABULARY_DB_PATH)
    new_vocab = load_json(NEW_VOCABULARY_PATH)
    
    print("\n" + "="*60)
    print("📊 词汇库统计")
    print("="*60)
    
    # 统计各风险等级词汇数量
    for risk_level in ["极高风险", "高风险", "中风险"]:
        count = len(vocab_db["scientific"].get(risk_level, {}))
        print(f"{risk_level}：{count}个词汇")
    
    # 专业领域统计
    print("\n专业领域词汇：")
    for domain, levels in vocab_db.get("professional", {}).items():
        total = sum(len(v) for v in levels.values())
        print(f"  - {domain}：{total}个")
    
    # 新词汇待确认
    new_count = len(new_vocab) if new_vocab else 0
    print(f"\n📋 待确认新词汇：{new_count}个")
    
    # 使用统计
    stats = vocab_db.get("stats", {})
    print(f"\n📈 使用统计：")
    print(f"  - 总检测次数：{stats.get('total_detections', 0)}")
    print(f"  - 新词汇添加：{stats.get('new_vocab_added', 0)}")
    print(f"  - 最后更新：{stats.get('last_updated', 'N/A')}")


def interactive_mode():
    """交互模式"""
    print("\n" + "="*60)
    print("🔧 AI内容幻觉检测器 - 词汇库管理工具")
    print("="*60)
    print("\n命令：")
    print("  1 - 查看待确认新词汇")
    print("  2 - 确认词汇（添加/删除）")
    print("  3 - 手动添加词汇")
    print("  4 - 查看词汇库统计")
    print("  q - 退出")
    
    while True:
        print("\n" + "-"*40)
        cmd = input("请输入命令：").strip()
        
        if cmd == 'q':
            print("👋 再见！")
            break
        
        elif cmd == '1':
            show_new_vocabulary()
        
        elif cmd == '2':
            show_new_vocabulary()
            new_vocab = load_json(NEW_VOCABULARY_PATH)
            if not new_vocab:
                continue
            
            try:
                index = int(input("\n请输入词汇序号："))
                action = input("操作（add添加/delete删除）：").strip()
                
                if action == 'delete':
                    confirm_vocabulary(index, 'delete')
                elif action == 'add':
                    risk_level = input("风险等级（极高风险/高风险/中风险）：").strip()
                    correct = input("正确语境（逗号分隔，可留空）：").strip()
                    pseudo = input("伪科学场景（逗号分隔，可留空）：").strip()
                    
                    correct_list = [x.strip() for x in correct.split(",")] if correct else []
                    pseudo_list = [x.strip() for x in pseudo.split(",")] if pseudo else []
                    
                    confirm_vocabulary(index, 'add', risk_level, correct_list, pseudo_list)
            except Exception as e:
                print(f"❌ 操作失败：{e}")
        
        elif cmd == '3':
            vocab = input("词汇名称：").strip()
            risk = input("风险等级（极高风险/高风险/中风险）：").strip()
            correct = input("正确语境（逗号分隔）：").strip()
            pseudo = input("伪科学场景（逗号分隔）：").strip()
            
            correct_list = [x.strip() for x in correct.split(",")] if correct else []
            pseudo_list = [x.strip() for x in pseudo.split(",")] if pseudo else []
            
            add_vocabulary_manually(vocab, risk, correct_list, pseudo_list)
        
        elif cmd == '4':
            show_vocabulary_stats()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'stats':
            show_vocabulary_stats()
        elif cmd == 'new':
            show_new_vocabulary()
        else:
            print(f"未知命令：{cmd}")
            print("可用命令：stats（统计）、new（新词汇）")
    else:
        interactive_mode()
