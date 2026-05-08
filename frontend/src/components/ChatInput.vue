<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/store/chat'
import { useWebSocket } from '@/composables/useWebSocket'

const store = useChatStore()
const { send } = useWebSocket()
const text = ref('')
const inputRef = ref<HTMLInputElement>()

function handleSend() {
  const t = text.value.trim()
  if (!t || store.isStreaming) return
  send('chat', t)
  text.value = ''
  inputRef.value?.focus()
}
</script>

<template>
  <div class="input-bar">
    <div class="input-wrapper">
      <input
        ref="inputRef"
        v-model="text"
        type="text"
        placeholder="输入消息..."
        :disabled="store.isStreaming"
        @keydown.enter="handleSend"
        autofocus
      />
      <button
        class="send-btn"
        :class="{ active: text.trim() && !store.isStreaming }"
        :disabled="store.isStreaming"
        @click="handleSend"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
      </button>
    </div>
    <div class="input-hint" v-if="!store.isStreaming">
      按 Enter 发送
    </div>
  </div>
</template>

<style scoped>
.input-bar{
  padding:14px 20px 16px;
  border-top:1px solid var(--border);
  flex-shrink:0;
  background:var(--bg-secondary);
}

.input-wrapper{
  display:flex;align-items:center;gap:8px;
  background:var(--bg-tertiary);
  border:1px solid var(--border);
  border-radius:var(--radius-lg);
  padding:4px 4px 4px 16px;
  transition:border-color .2s,box-shadow .2s;
}

.input-wrapper:focus-within{
  border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-glow);
}

input{
  flex:1;
  border:none;outline:none;
  background:transparent;
  color:var(--text-primary);
  font-size:14px;font-family:inherit;
  padding:8px 0;
}

input::placeholder{color:var(--text-muted)}
input:disabled{opacity:.5}

.send-btn{
  width:38px;height:38px;
  border:none;border-radius:50%;
  background:var(--bg-hover);
  color:var(--text-muted);
  cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:all .2s;flex-shrink:0;
}

.send-btn.active{
  background:var(--accent);
  color:#fff;
  box-shadow:0 2px 10px var(--accent-glow);
}

.send-btn.active:hover{
  background:var(--accent-light);
  transform:scale(1.05);
}

.send-btn:disabled{cursor:not-allowed}

.input-hint{
  text-align:center;font-size:10px;
  color:var(--text-muted);margin-top:6px;
}
</style>
