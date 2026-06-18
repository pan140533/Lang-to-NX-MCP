'use client'

import { useState, useRef, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Message, Feature } from './types'
import ViewControls from './components/ViewControls'

// 动态导入 ThreeViewer，禁用 SSR
const ThreeViewer = dynamic(() => import('./components/ThreeViewer'), {
  ssr: false,
  loading: () => (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="text-gray-400">加载 3D 渲染器...</div>
    </div>
  )
})

interface HistorySession {
  session_id: string
  part_file: string
  prt_exists: boolean
  features_count: number
  created_at: string
  last_active: string
  first_feature_type: string | null
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [features, setFeatures] = useState<Feature[]>([])
  const [showFeatures, setShowFeatures] = useState(true)
  const [showHistory, setShowHistory] = useState(false)
  const [historySessions, setHistorySessions] = useState<HistorySession[]>([])
  const [viewCommand, setViewCommand] = useState<'front' | 'top' | 'side' | 'reset' | null>(null)
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null)
  const [hoveredFeatureId, setHoveredFeatureId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 页面加载时从 localStorage 恢复会话
  useEffect(() => {
    const savedSessionId = localStorage.getItem('cad_session_id')
    if (savedSessionId) {
      restoreSession(savedSessionId)
    }
  }, [])

  // 加载历史会话列表
  const loadHistorySessions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/sessions')
      const data = await response.json()
      if (data.status === 'success') {
        setHistorySessions(data.sessions)
      }
    } catch (error) {
      console.error('加载历史会话失败:', error)
    }
  }

  // 切换历史面板时加载列表
  useEffect(() => {
    if (showHistory && historySessions.length === 0) {
      loadHistorySessions()
    }
  }, [showHistory])

  // 保存 sessionId 到 localStorage
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('cad_session_id', sessionId)
    } else {
      localStorage.removeItem('cad_session_id')
    }
  }, [sessionId])

  const restoreSession = async (sessionIdToRestore: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/session/${sessionIdToRestore}`)
      const data = await response.json()
      
      if (data.status === 'success' && data.session) {
        setSessionId(sessionIdToRestore)
        if (data.session.features) {
          setFeatures(data.session.features)
        }
      }
    } catch (error) {
      console.error('恢复会话失败:', error)
      localStorage.removeItem('cad_session_id')
    }
  }

  const loadHistorySession = async (historySession: HistorySession) => {
    setShowHistory(false)
    setMessages([])
    await restoreSession(historySession.session_id)
    setShowFeatures(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: input.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          description: input.trim()
        })
      })

      const data = await response.json()

      let assistantContent = ''
      if (data.status === 'success') {
        // 更新会话 ID
        if (data.session_id && !sessionId) {
          setSessionId(data.session_id)
        }

        // 更新特征列表
        if (data.features) {
          setFeatures(data.features)
        }

        // 构建响应消息
        assistantContent = `✓ ${data.message}\n\n`
        
        if (data.features && data.features.length > 0) {
          const lastFeature = data.features[data.features.length - 1]
          if (lastFeature.type === 'block') {
            const params = lastFeature.parameters
            assistantContent += `尺寸参数：\n• 长度: ${params.length} mm\n• 宽度: ${params.width} mm\n• 高度: ${params.height} mm\n`
          } else if (lastFeature.type === 'cylinder') {
            const params = lastFeature.parameters
            assistantContent += `尺寸参数：\n• 直径: ${params.diameter} mm\n• 高度: ${params.height} mm\n`
          } else if (lastFeature.type === 'cone') {
            const params = lastFeature.parameters
            assistantContent += `尺寸参数：\n• 底部直径: ${params.base_diameter} mm\n• 顶部直径: ${params.top_diameter} mm\n• 高度: ${params.height} mm\n`
          } else if (lastFeature.type === 'sphere') {
            const params = lastFeature.parameters
            assistantContent += `尺寸参数：\n• 直径: ${params.diameter} mm\n`
          }
          assistantContent += `\n当前零件共有 ${data.features.length} 个特征`
        }
      } else {
        assistantContent = `✗ 执行失败: ${data.message}`
      }

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: assistantContent
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '请求失败，请检查后端服务是否正常运行。'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewPart = () => {
    setSessionId(null)
    setFeatures([])
    setMessages([])
    setSelectedFeatureId(null)
    setHoveredFeatureId(null)
    localStorage.removeItem('cad_session_id')
  }

  const handleViewChange = (view: 'front' | 'top' | 'side' | 'reset') => {
    setViewCommand(view)
  }

  const handleViewChanged = () => {
    setViewCommand(null)
  }

  const getBooleanOpLabel = (op: string) => {
    const labels: Record<string, string> = {
      'create': '创建',
      'unite': '合并',
      'subtract': '减去',
      'intersect': '交集'
    }
    return labels[op] || op
  }

  const getFeatureIcon = (type: string) => {
    if (type === 'block') return '📦'
    if (type === 'cylinder') return '⚪'
    if (type === 'cone') return '🔺'
    if (type === 'sphere') return '🔮'
    return '❓'
  }

  const getFeatureLabel = (type: string) => {
    if (type === 'block') return '块'
    if (type === 'cylinder') return '圆柱'
    if (type === 'cone') return '圆锥'
    if (type === 'sphere') return '球'
    return type
  }

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* 左侧边栏 - 特征列表 */}
      <div className={`${showFeatures ? 'w-72' : 'w-0'} transition-all duration-300 bg-gray-800 border-r border-gray-700 overflow-hidden flex-shrink-0`}>
        <div className="p-4 h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-semibold">特征列表</h2>
            <button
              onClick={handleNewPart}
              className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              新建零件
            </button>
          </div>
          
          {sessionId && (
            <div className="text-xs text-gray-400 mb-4 break-all">
              会话: {sessionId}
            </div>
          )}

          <div className="flex-1 overflow-y-auto">
            {features.length === 0 ? (
              <div className="text-gray-500 text-sm text-center py-8">
                暂无特征
              </div>
            ) : (
              <div className="space-y-2">
                {features.map((feature, index) => (
                  <div
                    key={feature.feature_id}
                    className={`bg-gray-700 rounded-lg p-3 text-sm transition-all cursor-pointer border-2 ${
                      selectedFeatureId === feature.feature_id
                        ? 'border-yellow-500 bg-gray-600'
                        : hoveredFeatureId === feature.feature_id
                          ? 'border-blue-400 bg-gray-650'
                          : 'border-transparent hover:bg-gray-600'
                    }`}
                    onClick={() => setSelectedFeatureId(feature.feature_id)}
                    onMouseEnter={() => setHoveredFeatureId(feature.feature_id)}
                    onMouseLeave={() => setHoveredFeatureId(null)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{getFeatureIcon(feature.type)}</span>
                      <div className="flex-1">
                        <div className="text-white font-medium">
                          {getFeatureLabel(feature.type)} #{index + 1}
                        </div>
                        <div className="text-xs text-gray-400">
                          {getBooleanOpLabel(feature.boolean_op)}
                        </div>
                      </div>
                      {selectedFeatureId === feature.feature_id && (
                        <span className="text-xs text-yellow-500">✓</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-300 space-y-1">
                      {Object.entries(feature.parameters).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-400">{key}:</span>
                          <span>{value} mm</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 历史会话侧边栏 */}
      <div className={`${showHistory ? 'w-72' : 'w-0'} transition-all duration-300 bg-gray-800 border-r border-gray-700 overflow-hidden flex-shrink-0`}>
        <div className="p-4 h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-semibold">历史会话</h2>
            <button
              onClick={loadHistorySessions}
              className="text-gray-400 hover:text-white p-1"
              title="刷新"
            >
              🔄
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {historySessions.length === 0 ? (
              <div className="text-gray-500 text-sm text-center py-8">
                暂无历史会话
              </div>
            ) : (
              <div className="space-y-2">
                {historySessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`bg-gray-700 rounded-lg p-3 text-sm transition-all cursor-pointer border-2 ${
                      sessionId === session.session_id
                        ? 'border-yellow-500 bg-gray-600'
                        : 'border-transparent hover:bg-gray-600'
                    }`}
                    onClick={() => loadHistorySession(session)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{getFeatureIcon(session.first_feature_type || 'unknown')}</span>
                      <div className="flex-1">
                        <div className="text-white font-medium truncate">
                          {getFeatureLabel(session.first_feature_type || 'unknown')}
                        </div>
                        <div className="text-xs text-gray-400">
                          {session.features_count} 个特征
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {session.last_active ? new Date(session.last_active).toLocaleString('zh-CN', {
                        month: 'numeric',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      }) : ''}
                    </div>
                    {!session.prt_exists && (
                      <div className="text-xs text-red-400 mt-1">
                        ⚠️ PRT 文件缺失
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 中间区域 - 3D 预览 */}
      <div className="flex-1 flex flex-col bg-gray-850 min-w-0">
        {/* 预览工具栏 */}
        <div className="bg-gray-800 border-b border-gray-700 p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFeatures(!showFeatures)}
              className="text-gray-400 hover:text-white p-2 hover:bg-gray-700 rounded"
              title={showFeatures ? '隐藏特征列表' : '显示特征列表'}
            >
              {showFeatures ? '◀' : '▶'}
            </button>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`text-gray-400 hover:text-white p-2 hover:bg-gray-700 rounded ${showHistory ? 'bg-gray-700 text-white' : ''}`}
              title="历史会话"
            >
              📜
            </button>
            <div className="h-6 w-px bg-gray-700"></div>
            <h2 className="text-white font-medium">3D 预览</h2>
          </div>
          
          <div className="flex items-center gap-2">
            {/* 视图控制按钮 */}
            <ViewControls onViewChange={handleViewChange} />
          </div>
        </div>

        {/* 3D 渲染区域 */}
        <div className="flex-1 relative bg-gradient-to-br from-gray-900 via-gray-850 to-gray-900">
          {features.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">📦</div>
                <p className="text-gray-400 text-lg mb-2">暂无模型</p>
                <p className="text-gray-500 text-sm">创建特征后将在此显示 3D 预览</p>
              </div>
            </div>
          ) : (
            <div className="absolute inset-0">
              <ThreeViewer 
                features={features} 
                viewCommand={viewCommand}
                onViewChanged={handleViewChanged}
                selectedFeatureId={selectedFeatureId}
                onFeatureSelect={setSelectedFeatureId}
              />
            </div>
          )}

          {/* 坐标轴指示器（右下角） */}
          {features.length > 0 && (
            <div className="absolute bottom-4 right-4 w-20 h-20 bg-gray-800 bg-opacity-90 rounded-lg border border-gray-700 flex flex-col items-center justify-center text-xs font-mono">
              <div className="text-red-400 font-bold">+X</div>
              <div className="text-green-400 font-bold">+Y</div>
              <div className="text-blue-400 font-bold">+Z</div>
            </div>
          )}

          {/* 操作提示（左下角） */}
          {features.length > 0 && (
            <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-90 rounded-lg border border-gray-700 px-3 py-2 text-xs text-gray-300">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">🖱️</span>
                <span>左键: 旋转</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">🖱️</span>
                <span>右键: 平移</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">🖱️</span>
                <span>滚轮: 缩放</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 右侧边栏 - 聊天面板 */}
      <div className="w-96 flex flex-col bg-gray-800 border-l border-gray-700 flex-shrink-0">
        {/* 聊天工具栏 */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-white font-medium">AI 助手</h2>
            {features.length > 0 && (
              <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                {features.length} 个特征
              </span>
            )}
          </div>
        </div>

        {/* 聊天消息区域 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 py-8">
              <p className="text-lg mb-2">👋 你好！</p>
              <p className="text-sm mb-4">我可以帮你创建 CAD 模型</p>
              <div className="text-left bg-gray-700 rounded-lg p-3 text-xs">
                <p className="text-gray-300 mb-2 font-medium">试试这些指令：</p>
                <ul className="space-y-1 text-gray-400">
                  <li>• 创建一个长200宽150高100的块</li>
                  <li>• 在块上挖一个直径50的圆柱孔</li>
                  <li>• 加一个直径60高80的圆柱并合并</li>
                  <li>• 在块的顶部中心加一个圆柱</li>
                </ul>
              </div>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-100'
                }`}
              >
                <pre className="whitespace-pre-wrap font-sans text-sm">{message.content}</pre>
              </div>
            </div>
          ))}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="p-4 border-t border-gray-700">
          <form onSubmit={handleSubmit} className="flex flex-col gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
              disabled={isLoading}
              placeholder="输入建模指令... (Enter 发送, Shift+Enter 换行)"
              className="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
              rows={3}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {isLoading ? '处理中...' : '发送指令'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
