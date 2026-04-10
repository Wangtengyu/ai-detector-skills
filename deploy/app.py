# Vercel Serverless Function - AI Content Detector (Flask Style)
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

AI_PROVIDER = os.environ.get('AI_PROVIDER', 'deepseek')
AI_API_KEY = os.environ.get('AI_API_KEY', '')

def detect_with_deepseek(text, mode, detective='direnjie'):
    """使用DeepSeek模型进行检测"""
    if not AI_API_KEY:
        return None, "未配置AI_API_KEY"
    
    detective_names = {
        'direnjie': '狄仁杰', 'baoqing': '包青天', 'conan': '柯南',
        'holmes': '福尔摩斯', 'qinfeng': '秦风'
    }
    
    if mode == 'fun':
        system_prompt = f"""你是{detective_names.get(detective, '狄仁杰')}，一位侦探。分析文本中的虚假信息、营销陷阱。
用{detective_names.get(detective, '狄仁杰')}的风格输出检测报告。"""
    else:
        system_prompt = """你是专业内容审核专家。检测AI幻觉、伪科学表述、绝对化承诺、逻辑漏洞、营销骗局。
输出：风险等级(高危/中危/低危/安全)、问题列表、分析、建议。"""
    
    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'检测以下内容：\n\n{text}'}
                ],
                'max_tokens': 1024
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'], None
        else:
            return None, f"DeepSeek API错误: {response.status_code}"
    except Exception as e:
        return None, f"请求失败: {str(e)}"

# 关键词检测（备用）- 扩充版
PSEUDO = ['量子', '纳米', 'DNA', '干细胞', '基因修复', '能量场', '共振', '磁场', '远红外线', '负离子', '氢氧', '富氢', '量子共振', '纳米技术', '基因编辑', '端粒酶', '端粒修复', '线粒体', 'ATP', '生物电', '微电流']
ABSOLUTE = ['根治', '100%', '绝对', '保证', '包治', '无副作用', '零风险', '必', '包过', '必过', '百分百', '彻底治愈', '永不复发', '完全康复']
SCAM = ['原始股', '高额回报', '躺赚', '被动收入', '快速致富', '保本保息', '内部消息', '限量', '最后', '仅剩', '抢购', '买一送一', '限时', '特价', '优惠']
FAKE_ENDORSEMENT = ['NASA', '诺贝尔', '中科院', '国家专利', '央视推荐', '专家推荐', '三甲医院', '临床试验']

def detect_keywords(text):
    issues = []
    for kw in PSEUDO:
        if kw in text: issues.append(f'⚠️ 伪科学："{kw}"')
    for kw in ABSOLUTE:
        if kw in text: issues.append(f'❌ 绝对化："{kw}"')
    for kw in SCAM:
        if kw in text: issues.append(f'🚨 营销话术："{kw}"')
    for kw in FAKE_ENDORSEMENT:
        if kw in text: issues.append(f'🎭 疑似虚假背书："{kw}"')
    return issues

@app.route('/api/detect', methods=['POST', 'OPTIONS'])
def detect():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        mode = data.get('mode', 'serious')
        detective = data.get('detective', 'direnjie')
        
        if not text:
            return jsonify({'success': False, 'error': '请输入内容'}), 400
        
        # 调用AI模型
        ai_result, error = detect_with_deepseek(text, mode, detective)
        
        if ai_result:
            return jsonify({
                'success': True,
                'data': {
                    'risk_level': 'high' if '高危' in ai_result or '🚨' in ai_result else 'medium' if '中危' in ai_result else 'low',
                    'issues': [],
                    'report': ai_result,
                    'suggestions': [],
                    'ai_model': AI_PROVIDER
                }
            })
        else:
            # 回退到关键词检测
            issues = detect_keywords(text)
            risk = 'high' if len(issues) >= 4 else 'medium' if len(issues) >= 2 else 'low' if issues else 'safe'
            return jsonify({
                'success': True,
                'data': {
                    'risk_level': risk,
                    'issues': issues,
                    'report': f"检测到 {len(issues)} 处可疑内容。" if issues else "未检测到明显问题。",
                    'suggestions': ['删除高风险内容'] if risk == 'high' else [],
                    'ai_model': 'keywords',
                    'error': error
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'ai_provider': AI_PROVIDER,
        'has_api_key': bool(AI_API_KEY)
    })

# 启动服务
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
