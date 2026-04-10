# AI内容检测器 - 后端API（接入Claude模型）
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import os

app = Flask(__name__)
CORS(app)

# Claude API配置
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')

def detect_with_claude(text, mode, detective='direnjie'):
    """使用Claude模型进行检测"""
    if not CLAUDE_API_KEY:
        return None
    
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
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
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": f"检测以下内容：\n\n{text}"}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude API error: {e}")
        return None

# 关键词检测（备用）
PSEUDO = ['量子', '纳米', 'DNA', '干细胞', '基因修复', '能量场', '共振', '磁场']
ABSOLUTE = ['根治', '100%', '绝对', '保证', '包治', '无副作用', '零风险']
SCAM = ['原始股', '高额回报', '躺赚', '被动收入', '快速致富', '保本保息']

def detect_keywords(text):
    issues = []
    for kw in PSEUDO:
        if kw in text: issues.append(f'⚠️ 伪科学："{kw}"')
    for kw in ABSOLUTE:
        if kw in text: issues.append(f'❌ 绝对化："{kw}"')
    for kw in SCAM:
        if kw in text: issues.append(f'🚨 骗局："{kw}"')
    return issues

@app.route('/api/detect', methods=['POST'])
def detect():
    try:
        data = request.get_json()
        text, mode, detective = data.get('text', ''), data.get('mode', 'serious'), data.get('detective', 'direnjie')
        
        if not text:
            return jsonify({'success': False, 'error': '请输入内容'}), 400
        
        # 优先Claude，回退关键词
        claude_result = detect_with_claude(text, mode, detective)
        
        if claude_result:
            return jsonify({
                'success': True,
                'data': {
                    'risk_level': 'high' if '高危' in claude_result or '🚨' in claude_result else 'medium' if '中危' in claude_result else 'low',
                    'issues': [],
                    'report': claude_result,
                    'suggestions': [],
                    'ai_model': 'claude-3-5-sonnet'
                }
            })
        else:
            issues = detect_keywords(text)
            risk = 'high' if len(issues) >= 4 else 'medium' if len(issues) >= 2 else 'low' if issues else 'safe'
            return jsonify({
                'success': True,
                'data': {
                    'risk_level': risk,
                    'issues': issues,
                    'report': f"检测到 {len(issues)} 处可疑内容。" if issues else "未检测到明显问题。",
                    'suggestions': ['删除高风险内容'] if risk == 'high' else [],
                    'ai_model': 'keywords'
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'claude': bool(CLAUDE_API_KEY)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
