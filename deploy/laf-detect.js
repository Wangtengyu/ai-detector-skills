// Laf 云函数 - AI内容检测器
const axios = require('axios')

// AI配置
const AI_PROVIDER = process.env.AI_PROVIDER || 'deepseek'
const AI_API_KEY = process.env.AI_API_KEY || 'sk-eb51213b7bec4a5589536985e0d7a06e'

// 关键词库
const PSEUDO = ['量子', '纳米', 'DNA', '干细胞', '基因修复', '能量场', '共振', '磁场', '远红外线', '负离子', '氢氧', '富氢', '量子共振', '纳米技术', '基因编辑', '端粒酶', '端粒修复', '线粒体', 'ATP', '生物电', '微电流']
const ABSOLUTE = ['根治', '100%', '绝对', '保证', '包治', '无副作用', '零风险', '必', '包过', '必过', '百分百', '彻底治愈', '永不复发', '完全康复']
const SCAM = ['原始股', '高额回报', '躺赚', '被动收入', '快速致富', '保本保息', '内部消息', '限量', '最后', '仅剩', '抢购', '买一送一', '限时', '特价', '优惠']
const FAKE_ENDORSEMENT = ['NASA', '诺贝尔', '中科院', '国家专利', '央视推荐', '专家推荐', '三甲医院', '临床试验']

// DeepSeek AI检测
async function detectWithDeepSeek(text, mode, detective) {
  if (!AI_API_KEY) {
    return { result: null, error: '未配置AI_API_KEY' }
  }

  const detectiveNames = {
    'direnjie': '狄仁杰',
    'baoqing': '包青天', 
    'conan': '柯南',
    'holmes': '福尔摩斯',
    'qinfeng': '秦风'
  }

  let systemPrompt = ''
  if (mode === 'fun') {
    systemPrompt = `你是${detectiveNames[detective] || '狄仁杰'}，一位侦探。分析文本中的虚假信息、营销陷阱。用${detectiveNames[detective] || '狄仁杰'}的风格输出检测报告。`
  } else {
    systemPrompt = '你是专业内容审核专家。检测AI幻觉、伪科学表述、绝对化承诺、逻辑漏洞、营销骗局。输出：风险等级(高危/中危/低危/安全)、问题列表、分析、建议。'
  }

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

    return { result: response.data.choices[0].message.content, error: null }
  } catch (error) {
    return { result: null, error: error.message }
  }
}

// 关键词检测（备用）
function detectKeywords(text) {
  const issues = []
  PSEUDO.forEach(k => { if (text.includes(k)) issues.push(`⚠️ 伪科学："${k}"`) })
  ABSOLUTE.forEach(k => { if (text.includes(k)) issues.push(`❌ 绝对化："${k}"`) })
  SCAM.forEach(k => { if (text.includes(k)) issues.push(`🚨 营销话术："${k}"`) })
  FAKE_ENDORSEMENT.forEach(k => { if (text.includes(k)) issues.push(`🎭 疑似虚假背书："${k}"`) })
  return issues
}

// 云函数入口
export default async function (ctx: FunctionContext) {
  // 允许跨域
  ctx.set('Access-Control-Allow-Origin', '*')
  ctx.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  ctx.set('Access-Control-Allow-Headers', 'Content-Type')

  // OPTIONS请求直接返回
  if (ctx.method === 'OPTIONS') {
    return { status: 'ok' }
  }

  try {
    const body = ctx.body || {}
    const text = body.text || ''
    const mode = body.mode || 'serious'
    const detective = body.detective || 'direnjie'

    if (!text) {
      return { success: false, error: '请输入内容' }
    }

    // 调用AI
    const { result, error } = await detectWithDeepSeek(text, mode, detective)

    if (result) {
      return {
        success: true,
        data: {
          risk_level: result.includes('高危') || result.includes('🚨') ? 'high' : result.includes('中危') ? 'medium' : 'low',
          issues: [],
          report: result,
          suggestions: [],
          ai_model: AI_PROVIDER
        }
      }
    } else {
      // 回退到关键词检测
      const issues = detectKeywords(text)
      const risk = issues.length >= 4 ? 'high' : issues.length >= 2 ? 'medium' : issues.length >= 1 ? 'low' : 'safe'
      
      return {
        success: true,
        data: {
          risk_level: risk,
          issues: issues,
          report: issues.length > 0 ? `检测到 ${issues.length} 处可疑内容。` : '未检测到明显问题。',
          suggestions: risk === 'high' ? ['删除高风险内容'] : [],
          ai_model: 'keywords',
          error: error
        }
      }
    }
  } catch (error) {
    return { success: false, error: error.message }
  }
}
