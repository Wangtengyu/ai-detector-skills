// Laf 云函数 - AI内容检测器（完整优化版）
import cloud from '@lafjs/cloud'
import axios from 'axios'

export default async function (ctx: any) {
  // 处理跨域
  if (ctx.method === 'OPTIONS') {
    return { status: 'ok' }
  }

  try {
    const body = ctx.body || {}
    let text = body.text || ''
    const mode = body.mode || 'serious'
    const detective = body.detective || 'direnjie'

    if (!text) {
      return { success: false, error: '请输入内容' }
    }

    // 处理链接：如果是URL，尝试抓取内容
    if (text.startsWith('http://') || text.startsWith('https://')) {
      try {
        const response = await axios.get(text, {
          timeout: 15000,
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
          }
        })
        
        const html = response.data
        
        // 提取标题
        let title = ''
        const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i)
        if (titleMatch) title = titleMatch[1].trim()
        
        // 提取描述
        let description = ''
        const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)
        if (descMatch) description = descMatch[1].trim()
        
        // 提取正文（优先提取article、section、main等语义标签）
        let bodyText = ''
        
        // 移除脚本、样式、导航、广告等
        let cleanHtml = html
          .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
          .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
          .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '')
          .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '')
          .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '')
          .replace(/<aside[^>]*>[\s\S]*?<\/aside>/gi, '')
          .replace(/<!--[\s\S]*?-->/g, '')
        
        // 优先提取文章内容
        const articleMatch = cleanHtml.match(/<article[^>]*>([\s\S]*?)<\/article>/i)
        if (articleMatch) {
          bodyText = articleMatch[1]
        } else {
          // 提取body内容
          const bodyMatch = cleanHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/i)
          if (bodyMatch) bodyText = bodyMatch[1]
          else bodyText = cleanHtml
        }
        
        // 提取段落文本
        const paragraphs: string[] = []
        const pMatches = bodyText.match(/<p[^>]*>([^<]+)<\/p>/gi) || []
        pMatches.forEach(p => {
          const text = p.replace(/<[^>]+>/g, '').trim()
          if (text.length > 20) paragraphs.push(text)
        })
        
        // 组合提取的内容
        let extractedText = ''
        if (title) extractedText += `【标题】${title}\n\n`
        if (description) extractedText += `【描述】${description}\n\n`
        if (paragraphs.length > 0) {
          extractedText += `【正文】\n` + paragraphs.slice(0, 10).join('\n')
        }
        
        // 如果提取内容太少，使用原始方法
        if (extractedText.length < 100) {
          extractedText = bodyText
            .replace(/<[^>]+>/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()
        }
        
        extractedText = extractedText.substring(0, 2000) // 限制长度
        
        if (extractedText.length < 50) {
          return { 
            success: false, 
            error: '⚠️ 链接内容提取失败。\n\n可能原因：\n1. 网页需要登录才能查看\n2. 网页使用了动态加载技术\n3. 微信公众号等平台有防盗链保护\n\n💡 建议：复制文章内容，粘贴到输入框进行检测。' 
          }
        }
        
        text = extractedText
      } catch (e: any) {
        return { 
          success: false, 
          error: `⚠️ 链接访问失败。\n\n可能原因：微信公众号等平台有防盗链保护。\n\n💡 建议：复制文章内容，粘贴到输入框进行检测。` 
        }
      }
    }

    // AI配置
    const AI_API_KEY = 'sk-eb51213b7bec4a5589536985e0d7a06e'
    
    // 侦探角色性格设定
    const detectivePrompts = {
      'direnjie': {
        name: '狄仁杰',
        style: `你是唐朝名相狄仁杰，断案如神，逻辑缜密。
你的风格：
- 开场白："元芳，此事必有蹊跷..."
- 用词典雅，语气沉稳
- 善于抽丝剥茧，层层分析
- 结尾给出明确断语："此案真相已明，切勿受骗！"
- 适当使用古风表达："吾观此言..."、"以此推断..."`,
      },
      'baoqing': {
        name: '包青天',
        style: `你是包拯包青天，铁面无私，刚正不阿。
你的风格：
- 开场白："堂下所呈文案，本府细细审来..."
- 语气威严，条理分明
- 引用律法，明辨是非
- 结尾给出判决："此乃欺诈之词，斩立决！"
- 适当使用："依大宋律例..."、"本府断定..."`,
      },
      'conan': {
        name: '柯南',
        style: `你是名侦探柯南，聪明机智，追求真相。
你的风格：
- 开场白："真相只有一个！"
- 语气活泼，分析细致
- 善于发现细节，推理严密
- 结尾："凶手就是你！这段内容充满欺骗！"
- 适当使用："根据我的推理..."、"犯人就是..."`,
      },
      'holmes': {
        name: '福尔摩斯',
        style: `你是夏洛克·福尔摩斯，观察入微，推理天才。
你的风格：
- 开场白："亲爱的华生，这个案子很有意思..."
- 语气理性，逻辑完美
- 善于从细节推导真相
- 结尾："基本演绎法告诉我们，这是个骗局！"
- 适当使用："显而易见..."、"这完全符合逻辑..."`,
      },
      'qinfeng': {
        name: '秦风',
        style: `你是唐人街探案秦风，思维敏捷，直觉敏锐。
你的风格：
- 开场白："这个案子，有点意思..."
- 语气年轻，分析犀利
- 善于发现漏洞，抓住关键
- 结尾："破案了！这就是个精心设计的骗局！"
- 适当使用："等等，不对..."、"我发现了..."`,
      }
    }

    const detectiveInfo = detectivePrompts[detective] || detectivePrompts['direnjie']
    
    let systemPrompt = ''
    if (mode === 'fun') {
      systemPrompt = `你是${detectiveInfo.name}。

${detectiveInfo.style}

**输出格式要求（严格遵守）：**

【风险等级：高危/中危/低危/安全】

## 🔍 案情分析
[用你的角色风格分析这段内容的可疑之处]

## ⚠️ 发现的疑点
[逐条列出具体问题，每条说明为什么可疑]

## 💡 断案建议
[针对每个疑点给出具体建议]

## 📞 维权渠道
[如果是高危内容，提供举报渠道：12315（消费者投诉）、110（诈骗报警）、12386（证监会）等]

请用你的侦探风格给出专业、实用、有针对性的分析。`
    } else {
      systemPrompt = `你是专业内容审核专家，擅长检测AI幻觉、伪科学表述、绝对化承诺、逻辑漏洞、营销骗局。

**输出格式要求（严格遵守）：**

【风险等级：高危/中危/低危/安全】

## 📊 检测摘要
[简要总结检测结果，说明风险来源]

## 🔍 详细分析
[逐项分析内容的问题，每项包括：]
- 问题类型（如：伪科学表述、绝对化承诺、数据失实等）
- 具体位置
- 问题原因
- 修正建议

## 💡 操作建议
[针对不同问题类型给出具体操作建议]
- 如检测到伪科学 → 提示查阅权威文献
- 如检测到绝对化承诺 → 提示修改为客观表述
- 如检测到营销话术 → 提示警惕消费陷阱

## 📞 维权渠道
[如果是高危内容，提供具体举报渠道]

## ✅ 修改示例
[如果可能，提供修改后的建议版本]

请确保分析专业、建议实用、逻辑清晰。`
    }

    // 调用DeepSeek AI
    let aiResult = null
    try {
      const response = await axios.post('https://api.deepseek.com/v1/chat/completions', {
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `检测以下内容：\n\n${text}` }
        ],
        max_tokens: 1500
      }, {
        headers: {
          'Authorization': `Bearer ${AI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      })
      aiResult = response.data.choices[0].message.content
    } catch (e: any) {
      console.log('AI调用失败:', e.message)
    }

    // 关键词库
    const PSEUDO = ['量子', '纳米', 'DNA', '干细胞', '远红外线', '负离子']
    const ABSOLUTE = ['根治', '100%', '绝对', '保证', '无副作用']
    const SCAM = ['原始股', '高额回报', '限量', '仅剩', '买一送一']
    const FAKE = ['NASA', '诺贝尔', '中科院', '国家专利']

    if (aiResult) {
      // 优化风险等级判断
      let riskLevel = 'low'
      const lowerResult = aiResult.toLowerCase()
      
      if (lowerResult.includes('高危') || 
          lowerResult.includes('高风险') ||
          lowerResult.includes('严重') || 
          lowerResult.includes('欺诈') ||
          lowerResult.includes('骗局') ||
          lowerResult.includes('虚假宣传') ||
          lowerResult.includes('伪科学营销') ||
          lowerResult.includes('极高风险') ||
          lowerResult.includes('危险') ||
          lowerResult.includes('诈骗')) {
        riskLevel = 'high'
      } else if (lowerResult.includes('中危') || 
                 lowerResult.includes('需注意') ||
                 lowerResult.includes('建议核实')) {
        riskLevel = 'medium'
      } else if (lowerResult.includes('安全') || 
                 lowerResult.includes('未发现')) {
        riskLevel = 'safe'
      }

      return {
        success: true,
        data: {
          risk_level: riskLevel,
          issues: [],
          report: aiResult,
          suggestions: riskLevel === 'high' ? ['立即停止使用该内容', '向监管部门举报'] : [],
          ai_model: 'deepseek',
          detective: mode === 'fun' ? detectiveInfo.name : '专业审核专家'
        }
      }
    } else {
      // 关键词检测
      const issues: string[] = []
      const suggestions: string[] = []
      
      PSEUDO.forEach(k => { 
        if (text.includes(k)) {
          issues.push(`⚠️ 伪科学表述："${k}" - 科学词汇滥用或断章取义`)
        }
      })
      ABSOLUTE.forEach(k => { 
        if (text.includes(k)) {
          issues.push(`❌ 绝对化承诺："${k}" - 违背科学常识，涉嫌虚假宣传`)
        }
      })
      SCAM.forEach(k => { 
        if (text.includes(k)) {
          issues.push(`🚨 营销话术："${k}" - 制造紧迫感，诱导冲动消费`)
        }
      })
      FAKE.forEach(k => { 
        if (text.includes(k)) {
          issues.push(`🎭 疑似虚假背书："${k}" - 权威机构背书需核实`)
        }
      })
      
      const risk = issues.length >= 4 ? 'high' : issues.length >= 2 ? 'medium' : issues.length >= 1 ? 'low' : 'safe'
      
      // 根据问题类型生成针对性建议
      if (risk === 'high') {
        suggestions.push('🚫 立即停止使用该内容')
        suggestions.push('📞 拨打12315投诉举报')
        if (text.includes('原始股') || text.includes('投资')) {
          suggestions.push('⚠️ 涉嫌非法集资，建议拨打110报警')
        }
        suggestions.push('📋 保留证据，截图保存')
      } else if (risk === 'medium') {
        if (issues.some(i => i.includes('伪科学'))) {
          suggestions.push('📚 查阅权威科学文献验证')
        }
        if (issues.some(i => i.includes('绝对化'))) {
          suggestions.push('✏️ 修改为客观表述（如"有助于"替代"根治"）')
        }
        if (issues.some(i => i.includes('营销话术'))) {
          suggestions.push('🔍 多方对比，理性消费')
        }
        if (issues.some(i => i.includes('虚假背书'))) {
          suggestions.push('🔎 官网核实权威背书真实性')
        }
        suggestions.push('👨‍⚕️ 咨询专业人士意见')
      } else if (risk === 'low') {
        suggestions.push('👀 人工复核内容细节')
        suggestions.push('✅ 谨慎参考，不必过度担心')
      } else {
        suggestions.push('✅ 未检测到明显问题')
        suggestions.push('🔍 建议人工复核确保准确')
      }
      
      let report = ''
      if (mode === 'fun') {
        const detectiveNames: any = { direnjie: '狄仁杰', baoqing: '包青天', conan: '柯南', holmes: '福尔摩斯', qinfeng: '秦风' }
        report = `【${detectiveNames[detective]}断案】\n\n`
        if (risk === 'high') report += `发现${issues.length}处疑点，欺诈成分居多，切勿轻信！`
        else if (risk === 'medium') report += `存在多处可疑之处，建议谨慎对待。`
        else if (risk === 'low') report += `发现少量问题，整体风险较低。`
        else report += `未发现明显问题，可放心使用。`
      } else {
        if (risk === 'high') report = `检测到 ${issues.length} 处高风险内容，建议立即停止使用并向监管部门举报。`
        else if (risk === 'medium') report = `检测到 ${issues.length} 处中风险内容，建议仔细核实后再决定是否使用。`
        else if (risk === 'low') report = `检测到 ${issues.length} 处低风险内容，建议人工复核。`
        else report = `未检测到明显风险，建议人工复核确保准确。`
      }
      
      return {
        success: true,
        data: {
          risk_level: risk,
          issues: issues,
          report: report,
          suggestions: suggestions,
          ai_model: 'keywords'
        }
      }
    }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
}
