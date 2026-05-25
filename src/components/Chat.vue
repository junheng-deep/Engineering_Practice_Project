<template>
  <div class="min-h-screen bg-gray-100 flex">
    <aside 
      class="w-72 bg-white border-r border-gray-200 flex flex-col"
      :class="{ 'hidden lg:flex': !showSidebar }"
    >
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800">历史对话</h2>
          <button
            @click="toggleSidebar"
            class="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
          </button>
        </div>
        
        <button
          @click="startNewChat"
          class="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-2 px-4 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all"
        >
          + 新对话
        </button>
      </div>

      <div class="flex-1 overflow-y-auto scrollbar-thin">
        <div v-if="chatHistory.length === 0" class="p-4 text-center text-gray-400">
          <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
          <p>暂无历史对话</p>
        </div>

        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          @click="loadChatHistory(chat.id)"
          class="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
          :class="{ 'bg-blue-50': activeChatId === chat.id }"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-800 truncate">{{ chat.title }}</p>
              <p class="text-sm text-gray-500 truncate">{{ chat.lastMessage }}</p>
            </div>
            <button
              @click.stop="deleteChat(chat.id)"
              class="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
          <p class="text-xs text-gray-400 mt-1">{{ chat.time }}</p>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col">
      <header class="bg-white shadow-sm">
        <div class="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <button
              @click="toggleSidebar"
              class="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path>
              </svg>
            </button>
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
            </div>
            <div>
              <h1 class="text-lg font-semibold text-gray-800">智能体助手</h1>
              <p class="text-xs text-gray-500">在线</p>
            </div>
          </div>
          <button
            @click="handleLogout"
            class="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
            </svg>
            <span>退出登录</span>
          </button>
        </div>
      </header>

      <main class="flex-1 overflow-hidden">
        <div 
          ref="messagesContainer"
          class="max-w-4xl mx-auto px-4 py-6 h-full overflow-y-auto scrollbar-thin"
        >
          <div class="space-y-6">
            <div class="text-center">
              <div class="inline-flex items-center px-4 py-2 bg-gray-200 rounded-full">
                <span class="text-sm text-gray-600">欢迎回来！我是您的智能助手，有什么可以帮您的？</span>
              </div>
            </div>

            <div 
              v-for="(message, index) in messages" 
              :key="index"
              class="flex"
              :class="message.isUser ? 'justify-end' : 'justify-start'"
            >
              <div 
                class="max-w-md px-4 py-3 rounded-2xl"
                :class="message.isUser 
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-br-md' 
                  : 'bg-white text-gray-800 rounded-bl-md shadow-sm'"
              >
                <p class="text-sm">{{ message.content }}</p>
                <div 
                  class="mt-1 text-xs opacity-70 flex items-center justify-end"
                >
                  <span>{{ message.time }}</span>
                </div>
              </div>
            </div>

            <div v-if="isTyping" class="flex justify-start">
              <div class="bg-white px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
                <div class="flex space-x-2">
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer class="bg-white border-t border-gray-200">
        <div class="max-w-4xl mx-auto px-4 py-4">
          <div class="flex items-end space-x-3">
            <div class="flex-1">
              <div class="relative">
                <textarea
                  v-model="inputMessage"
                  @keydown.enter.exact.prevent="sendMessage"
                  placeholder="输入消息..."
                  rows="1"
                  class="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none outline-none transition-all"
                ></textarea>
                <button
                  @click="clearInput"
                  class="absolute right-3 bottom-3 text-gray-400 hover:text-gray-600 transition-colors"
                  :disabled="!inputMessage.trim()"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>
            </div>
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isTyping"
              class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 focus:ring-4 focus:ring-blue-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
            </button>
          </div>
          <p class="text-xs text-gray-400 text-center mt-2">
            按 Enter 发送消息
          </p>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const messages = ref([])
const inputMessage = ref('')
const isTyping = ref(false)
const messagesContainer = ref(null)
const showSidebar = ref(false)
const activeChatId = ref(null)
const chatHistory = ref([])

const greetings = [
  '您好！有什么我可以帮助您的吗？',
  '很高兴为您服务！请问有什么需求？',
  '您好！我是您的智能助手，随时为您解答问题。',
  '嗨！需要什么帮助吗？',
  '您好！请问我可以帮您做什么？'
]

const responses = [
  '这是一个很好的问题！让我为您详细解答...',
  '感谢您的提问，我来为您分析一下。',
  '好的，我理解您的需求。以下是我的建议：',
  '根据您的问题，我认为可以这样处理：',
  '这是一个很有意思的话题，让我们来探讨一下。',
  '我来帮您分析一下这个问题。',
  '感谢您的反馈，这对我很有帮助！',
  '好的，我明白了。让我为您提供更多信息。',
  '这个问题很重要，让我仔细思考一下...',
  '我可以理解您的困惑，让我为您解释清楚。'
]

const getTime = () => {
  const now = new Date()
  return now.toLocaleString('zh-CN', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const getFullTime = () => {
  const now = new Date()
  return now.toLocaleString('zh-CN', { 
    year: 'numeric',
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const saveChatHistory = () => {
  if (messages.value.length <= 1) return
  
  const user = JSON.parse(localStorage.getItem('user'))
  if (!user) return

  const chatData = {
    id: activeChatId.value || Date.now(),
    userId: user.id,
    title: messages.value[1]?.content?.substring(0, 30) + '...' || '新对话',
    lastMessage: messages.value[messages.value.length - 1]?.content?.substring(0, 50) + '...' || '',
    time: getFullTime(),
    messages: messages.value
  }

  let history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  const existingIndex = history.findIndex(c => c.id === chatData.id)
  
  if (existingIndex >= 0) {
    history[existingIndex] = chatData
  } else {
    history.unshift(chatData)
  }
  
  localStorage.setItem('chatHistory', JSON.stringify(history))
  loadChatHistoryList()
}

const loadChatHistoryList = () => {
  const user = JSON.parse(localStorage.getItem('user'))
  if (!user) return
  
  const history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  chatHistory.value = history.filter(c => c.userId === user.id)
}

const loadChatHistory = (chatId) => {
  const history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  const chat = history.find(c => c.id === chatId)
  
  if (chat) {
    messages.value = [...chat.messages]
    activeChatId.value = chatId
    showSidebar.value = false
    scrollToBottom()
  }
}

const deleteChat = (chatId) => {
  let history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  history = history.filter(c => c.id !== chatId)
  localStorage.setItem('chatHistory', JSON.stringify(history))
  loadChatHistoryList()
  
  if (activeChatId.value === chatId) {
    startNewChat()
  }
}

const startNewChat = () => {
  const user = JSON.parse(localStorage.getItem('user'))
  if (!user) {
    router.push('/')
    return
  }
  
  const greeting = {
    content: `您好，学号${user.username}！${greetings[Math.floor(Math.random() * greetings.length)]}`,
    isUser: false,
    time: getTime()
  }
  
  messages.value = [greeting]
  activeChatId.value = null
  showSidebar.value = false
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isTyping.value) return

  const userMessage = {
    content: inputMessage.value.trim(),
    isUser: true,
    time: getTime()
  }
  
  messages.value.push(userMessage)
  inputMessage.value = ''
  
  await scrollToBottom()
  
  isTyping.value = true
  
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))
  
  const botResponse = {
    content: responses[Math.floor(Math.random() * responses.length)] + '\n\n根据您的输入，我理解您想要了解相关信息。我会尽力为您提供帮助和支持。如果您有更多问题，随时可以继续提问！',
    isUser: false,
    time: getTime()
  }
  
  messages.value.push(botResponse)
  isTyping.value = false
  
  await scrollToBottom()
  
  saveChatHistory()
}

const clearInput = () => {
  inputMessage.value = ''
}

const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

const handleLogout = () => {
  localStorage.removeItem('user')
  router.push('/')
}

watch(messages, () => {
  if (messages.value.length > 1) {
    saveChatHistory()
  }
}, { deep: true })

onMounted(() => {
  const user = JSON.parse(localStorage.getItem('user'))
  if (!user) {
    router.push('/')
    return
  }
  
  loadChatHistoryList()
  
  const greeting = {
    content: `您好，学号${user.username}！${greetings[Math.floor(Math.random() * greetings.length)]}`,
    isUser: false,
    time: getTime()
  }
  messages.value = [greeting]
})
</script>
