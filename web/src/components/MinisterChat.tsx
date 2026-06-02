import { useState, useEffect, useRef } from 'react'
import { api } from '../api'
import { ScrollText, Send, User } from 'lucide-react'

interface Message {
  id: number
  role: 'emperor' | 'minister'
  text: string
  timestamp: string
}

interface MinisterChatProps {
  campaignId: string
  ministers: { id: number; name: string; position: string; faction: string }[]
  onMinisterSelect?: (name: string) => void
}

export function MinisterChat({ campaignId, ministers, onMinisterSelect }: MinisterChatProps) {
  const [selectedMinister, setSelectedMinister] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState<Record<string, Message[]>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (selectedMinister && chatHistory[selectedMinister]) {
      setMessages(chatHistory[selectedMinister])
    } else {
      setMessages([])
    }
  }, [selectedMinister, chatHistory])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSelectMinister = (name: string) => {
    setSelectedMinister(name)
    onMinisterSelect?.(name)
  }

  const handleSend = async () => {
    if (!input.trim() || !selectedMinister || loading) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'emperor',
      text: input.trim(),
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages(prev => [...prev, userMessage])
    setChatHistory(prev => ({ ...prev, [selectedMinister]: [...(prev[selectedMinister] || []), userMessage] }))
    setInput('')
    setLoading(true)

    try {
      const response = await api.chatWithMinister(campaignId, selectedMinister, input)
      const ministerMessage: Message = {
        id: Date.now() + 1,
        role: 'minister',
        text: response.result || '臣...遵旨。',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, ministerMessage])
      setChatHistory(prev => ({ ...prev, [selectedMinister]: [...(prev[selectedMinister] || []), ministerMessage] }))
    } catch (e) {
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'minister',
        text: '臣有要事禀报...（网络错误）',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, errorMessage])
    }
    setLoading(false)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="minister-chat">
      <div className="chat-ministers-list">
        <div className="chat-ministers-header">
          <ScrollText size={16} />
          <span>召见大臣</span>
        </div>
        <div className="chat-ministers">
          {ministers.map(m => (
            <div
              key={m.id}
              className={`chat-ministers-item ${selectedMinister === m.name ? 'chat-ministers-item--selected' : ''}`}
              onClick={() => handleSelectMinister(m.name)} role="button" tabIndex={0}
            >
              <div className="chat-ministers-avatar">
                {m.name.charAt(0)}
              </div>
              <div className="chat-ministers-info">
                <div className="chat-ministers-name">{m.name}</div>
                <div className="chat-ministers-position">{m.position}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="chat-main">
        {!selectedMinister ? (
          <div className="chat-empty">
            <User size={48} strokeWidth={1} />
            <p>请选择一位大臣召见</p>
          </div>
        ) : (
          <>
            <div className="chat-header">
              <div className="chat-header-info">
                <span className="chat-header-name">{selectedMinister}</span>
                <span className="chat-header-position">
                  {ministers.find(m => m.name === selectedMinister)?.position || ''}
                </span>
              </div>
            </div>

            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="chat-welcome">
                  <p>召见{selectedMinister}...</p>
                  <p className="chat-welcome-hint">可以询问政事、试探忠诚、或寻求建议</p>
                </div>
              )}
              {messages.map(msg => (
                <div key={msg.id} className={`chat-message chat-message--${msg.role}`}>
                  <div className="chat-message-bubble">
                    <div className="chat-message-text">{msg.text}</div>
                    <div className="chat-message-time">{msg.timestamp}</div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="chat-message chat-message--minister">
                  <div className="chat-message-bubble">
                    <div className="chat-message-text chat-message-thinking">臣在思量...</div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
              <textarea
                className="chat-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`对${selectedMinister}说...`}
                rows={2}
              />
              <button type="button"
                className="btn btn--primary chat-send"
                onClick={handleSend}
                disabled={!input.trim() || loading}
                aria-label="发送消息"
              >
                <Send size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}