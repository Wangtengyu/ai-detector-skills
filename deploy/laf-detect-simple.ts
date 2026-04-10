// Laf 云函数 - AI内容检测器（简化版）
import cloud from '@lafjs/cloud'
import axios from 'axios'

export default async function (ctx: any) {
  // 处理跨域
  if (ctx.method === 'OPTIONS') {
    return {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      },
      body: { status: 'ok' }
    }
  }

  try {
    const body = ctx.body || {}
    const text = body.text || ''
    const mode = body.mode || 'serious'
    const detective = body.detective || 'direnjie'

    if (!text) {
      return {
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: { success: false, error: '请输入内容' }
      }
    }

    // AI配置
    const AI_API_KEY = 'sk-eb51213b7bec4a5589536985e0d7a06e'
    
    const detectiveNames = {
      'direnjie': '狄仁杰',
      'baoqing': '包青天', 
      'conan': '柯南',
      'holmes': '福尔摩斯',
      'qinfeng': '秦风'
    }

    let systemPrompt = mode === 'fun' 
      ? `你是${detectiveNames[detective] || '狄仁杰'}，一位侦探。分析文本中的虚假信息、营销陷阱。`
      : '你是专业内容审核专家。检测AI幻觉、伪科学表述、绝对化承诺、逻辑漏洞、营销骗局。'

    // 调用DeepSeek AI
    let aiResult = null
    try {
      const response = await axios.post('https://api.deepseek.com/v1/chat/completions', {
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `检测以下内容：\n\n${text}` }
        ],
        max_tokens: 1024
      }, {
        headers: {
          'Authorization': `Bearer ${AI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      })
      aiResult = response.data.choices[0].message.content
    } catch (e) {
      console.log('AI调用失败:', e.message)
    }

    // 关键词库
    const PSEUDO = ['量子', '纳米', 'DNA', '干细胞', '远红外线', '负离子']
    const ABSOLUTE = ['根治', '100%', '绝对', '保证', '无副作用']
    const SCAM = ['原始股', '高额回报', '限量', '仅剩', '买一送一']
    const FAKE = ['NASA', '诺贝尔', '中科院', '国家专利']

    if (aiResult) {
      return {
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: {
          success: true,
          data: {
            risk_level: aiResult.includes('高危') ? 'high' : aiResult.includes('中危') ? 'medium' : 'low',
            issues: [],
            report: aiResult,
            suggestions: [],
            ai_model: 'deepseek'
          }
        }
      }
    } else {
      // 关键词检测
      const issues = []
      PSEUDO.forEach(k => { if (text.includes(k)) issues.push(`⚠️ 伪科学："${k}"`) })
      ABSOLUTE.forEach(k => { if (text.includes(k)) issues.push(`❌ 绝对化："${k}"`) })
      SCAM.forEach(k => { if (text.includes(k)) issues.push(`🚨 营销话术："${k}"`) })
      FAKE.forEach(k => { if (text.includes(k)) issues.push(`🎭 疑似虚假背书："${k}"`) })
      
      const risk = issues.length >= 4 ? 'high' : issues.length >= 2 ? 'medium' : issues.length >= 1 ? 'low' : 'safe'
      
      return {
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: {
          success: true,
          data: {
            risk_level: risk,
            issues: issues,
            report: issues.length > 0 ? `检测到 ${issues.length} 处可疑内容。` : '未检测到明显问题。',
            suggestions: risk === 'high' ? ['删除高风险内容'] : [],
            ai_model: 'keywords'
          }
        }
      }
    }
  } catch (error) {
    return {
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: { success: false, error: error.message }
    }
  }
}
