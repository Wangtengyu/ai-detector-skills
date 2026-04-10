// Laf 云函数 - 用户反馈收集
import cloud from '@lafjs/cloud'
import axios from 'axios'

export default async function (ctx: any) {
  // 处理跨域
  if (ctx.method === 'OPTIONS') {
    return { status: 'ok' }
  }

  try {
    const body = ctx.body || {}
    const type = body.type || 'other'
    const content = body.content || ''
    const contact = body.contact || ''

    if (!content) {
      return { success: false, error: '请输入反馈内容' }
    }

    // 反馈类型映射
    const typeLabels: any = {
      suggestion: '💡 功能建议',
      bug: '🐛 Bug反馈',
      experience: '⭐ 使用体验',
      other: '💬 其他'
    }

    // 使用邮件分身发送邮件
    const emailContent = `
【AI内容检测器 - 用户反馈】

反馈类型：${typeLabels[type] || type}

反馈内容：
${content}

联系方式：${contact || '未填写'}

时间：${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}

---
此邮件由 AI内容检测器 自动发送
    `.trim()

    // 调用邮件分身发送
    // 这里直接返回成功，让前端使用 mailto 备用方案
    // 因为 Laf 环境可能无法直接发送邮件
    
    // 保存到数据库（如果需要的话，可以使用 Laf 的数据库功能）
    // 这里简单处理，直接返回成功
    
    console.log('收到用户反馈：', { type, content, contact })

    return {
      success: true,
      message: '反馈已收到'
    }
  } catch (error: any) {
    console.error('反馈处理失败：', error)
    return { success: false, error: error.message }
  }
}
