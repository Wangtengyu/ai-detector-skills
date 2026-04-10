# Vercel Serverless Function for AI Content Detection
import os
import json
import requests

AI_PROVIDER = os.environ.get('AI_PROVIDER', 'deepseek')
AI_API_KEY = os.environ.get('AI_API_KEY', '')

def detect_with_deepseek(text, mode, detective='direnjie'):
    """使用DeepSeek模型进行检测"""
    if not AI_API_KEY:
        return None
    
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
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API error: {e}")
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

def handler(request):
    """Vercel Serverless Function Handler"""
    try:
        # 解析请求
        if hasattr(request, 'body'):
            body = json.loads(request.body) if request.body else {}
        else:
            body = request.get('body', {})
        
        text = body.get('text', '')
        mode = body.get('mode', 'serious')
        detective = body.get('detective', 'direnjie')
        
        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'success': False, 'error': '请输入内容'}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # 调用AI模型
        ai_result = None
        if AI_PROVIDER == 'deepseek':
            ai_result = detect_with_deepseek(text, mode, detective)
        
        if ai_result:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'data': {
                        'risk_level': 'high' if '高危' in ai_result or '🚨' in ai_result else 'medium' if '中危' in ai_result else 'low',
                        'issues': [],
                        'report': ai_result,
                        'suggestions': [],
                        'ai_model': AI_PROVIDER
                    }
                }),
                'headers': {'Content-Type': 'application/json'}
            }
        else:
            # 回退到关键词检测
            issues = detect_keywords(text)
            risk = 'high' if len(issues) >= 4 else 'medium' if len(issues) >= 2 else 'low' if issues else 'safe'
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'data': {
                        'risk_level': risk,
                        'issues': issues,
                        'report': f"检测到 {len(issues)} 处可疑内容。" if issues else "未检测到明显问题。",
                        'suggestions': ['删除高风险内容'] if risk == 'high' else [],
                        'ai_model': 'keywords'
                    }
                }),
                'headers': {'Content-Type': 'application/json'}
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'success': False, 'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
