/**
 * InsightIQ — AI Chat
 */

import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../lib/api'
import { MessageSquare, Send, Loader2, Sparkles, User, FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Props {
  datasetId: string | null
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  suggestedQuestions?: string[]
}

export default function AIChat({ datasetId }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am InsightIQ, your enterprise AI analyst. How can I help you analyze your dataset today?',
      suggestedQuestions: [
        'Give me a summary of this dataset',
        'What are the main trends?',
        'Are there any anomalies?'
      ]
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleSend = async (text: string) => {
    if (!text.trim() || !datasetId || isLoading) return

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const res = await sendChatMessage(datasetId, text)
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.response,
        sources: res.sources,
        suggestedQuestions: res.suggested_questions
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err: unknown) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `**Error:** Failed to analyze data. ${err instanceof Error ? err.message : String(err)}`
      }])
    } finally {
      setIsLoading(false)
    }
  }

  if (!datasetId) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <MessageSquare size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
        <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>AI Chat</h2>
        <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to chat with the AI Analyst</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in h-[calc(100vh-8rem)] flex flex-col">
      <div className="page-header mb-4">
        <h1 className="page-title">AI Analyst Chat</h1>
        <p className="page-subtitle">Ask questions in natural language. Powered by Google Gemini.</p>
      </div>

      <div className="card flex-1 flex flex-col overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.map(msg => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {/* Avatar */}
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1"
                   style={{ 
                     background: msg.role === 'user' ? 'var(--color-surface)' : 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
                     border: msg.role === 'user' ? '1px solid var(--color-border)' : 'none',
                     color: msg.role === 'user' ? 'var(--color-text-secondary)' : 'white'
                   }}>
                {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
              </div>
              
              {/* Message Bubble */}
              <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-5 py-4 ${
                msg.role === 'user' 
                  ? 'bg-blue-50 text-slate-900 border border-blue-100 rounded-tr-sm' 
                  : 'bg-white border border-slate-200 shadow-sm rounded-tl-sm'
              }`}>
                {msg.role === 'assistant' && (
                  <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--color-primary)' }}>
                    InsightIQ Analyst
                  </div>
                )}
                
                <div className="prose prose-sm max-w-none text-slate-700 prose-p:leading-relaxed prose-headings:font-bold prose-a:text-blue-600 prose-strong:text-slate-900">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {/* Sources & Suggestions */}
                {msg.role === 'assistant' && (
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="flex items-center gap-2 mb-3 text-xs text-slate-500">
                        <FileText size={12} />
                        <span>Sources: {msg.sources.join(', ')}</span>
                      </div>
                    )}
                    
                    {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {msg.suggestedQuestions.map((q, i) => (
                          <button
                            key={i}
                            onClick={() => handleSend(q)}
                            disabled={isLoading}
                            className="text-xs px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-full border border-slate-200 transition-colors"
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1"
                   style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))', color: 'white' }}>
                <Sparkles size={16} />
              </div>
              <div className="bg-white border border-slate-200 shadow-sm rounded-2xl rounded-tl-sm px-5 py-4">
                <div className="flex items-center gap-2 text-slate-500 text-sm">
                  <Loader2 size={16} className="animate-spin" />
                  Analyzing dataset...
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-slate-50 border-t border-slate-200">
          <form 
            onSubmit={e => { e.preventDefault(); handleSend(input) }}
            className="flex items-center gap-2 max-w-4xl mx-auto relative"
          >
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask anything about your data..."
              disabled={isLoading}
              className="flex-1 bg-white border border-slate-300 rounded-full pl-5 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center disabled:opacity-50 hover:bg-blue-700 transition-colors"
            >
              <Send size={14} />
            </button>
          </form>
          <div className="text-center mt-2 text-xs text-slate-400">
            AI can make mistakes. Consider verifying important metrics on the dashboard.
          </div>
        </div>
      </div>
    </div>
  )
}
