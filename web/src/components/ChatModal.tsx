import { useState, useEffect, useRef, useCallback } from 'react'
import { X, Send, User, Crown } from 'lucide-react'

interface ChatMessage {
  id: string
  role: 'emperor' | 'minister'
  text: string
  timestamp: string
}

interface Minister {
  id: number
  name: string
  position: string
  faction: string
  portrait?: string
}

interface ChatModalProps {
  isOpen: boolean
  onClose: () => void
  campaignId: string
  minister: Minister | null
  onSendMessage: (message: string) => Promise<string>
}

export function ChatModal({ isOpen, onClose, campaignId, minister, onSendMessage }: ChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamText, setStreamText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamText])

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading || !minister) return

    const userMsg: ChatMessage = {
      id: `emp-${Date.now()}`,
      role: 'emperor',
      text: input.trim(),
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setStreamText('')

    try {
      const fullResponse = await onSendMessage(userMsg.text)
      const ministerMsg: ChatMessage = {
        id: `min-${Date.now()}`,
        role: 'minister',
        text: fullResponse,
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, ministerMsg])
    } catch {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'minister',
        text: '臣...有事上奏。（网络异常）',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, errorMsg])
    }

    setLoading(false)
    setStreamText('')
  }, [input, loading, minister, onSendMessage])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClose = () => {
    setMessages([])
    setInput('')
    setStreamText('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="chat-modal" onClick={e => e.stopPropagation()}>
        <div className="chat-modal__header">
          <div className="chat-modal__minister-info">
            <div className="chat-modal__avatar">
              {minister?.portrait ? (
                <img src={minister.portrait} alt={minister.name} />
              ) : (
                <User size={24} />
              )}
            </div>
            <div>
              <div className="chat-modal__minister-name">{minister?.name || '未知大臣'}</div>
              <div className="chat-modal__minister-position">{minister?.position || ''}</div>
            </div>
          </div>
          <button className="chat-modal__close" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        <div className="chat-modal__messages">
          {messages.length === 0 && (
            <div className="chat-modal__welcome">
              <Crown size={32} strokeWidth={1} />
              <p>召见{minister?.name || '大臣'}问政</p>
              <p className="chat-modal__hint">可询问政事、试探忠诚、寻求建议</p>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`chat-modal__message chat-modal__message--${msg.role}`}>
              <div className="chat-modal__bubble">
                <div className="chat-modal__text">{msg.text}</div>
                <div className="chat-modal__time">{msg.timestamp}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-modal__message chat-modal__message--minister">
              <div className="chat-modal__bubble">
                <div className="chat-modal__text chat-modal__thinking">
                  {streamText || '臣在思量...'}
                  <span className="chat-modal__cursor">▊</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-modal__input-area">
          <textarea
            ref={inputRef}
            className="chat-modal__input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={minister ? `对${minister.name}说...` : '选择大臣后输入...'}
            rows={2}
            disabled={!minister || loading}
          />
          <button
            className="btn btn--primary chat-modal__send"
            onClick={handleSend}
            disabled={!input.trim() || loading || !minister}
            aria-label="发送消息"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}