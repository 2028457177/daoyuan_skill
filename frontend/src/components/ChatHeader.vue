<script setup lang="ts">
import { useChatStore } from '@/store/chat'
import { useWebSocket } from '@/composables/useWebSocket'

const store = useChatStore()
const { send } = useWebSocket()
</script>

<template>
  <header class="header">
    <div class="header-left">
      <div class="avatar-ring" :class="{ connected: store.isConnected }">
        <img class="avatar" :src="store.counselorInfo.avatar" alt="" />
      </div>
      <div class="header-info">
        <div class="header-name">
          {{ store.counselorInfo.name }}
          <span class="verified">✓</span>
        </div>
        <div class="header-status">
          <span class="status-dot" :class="{ online: store.isConnected }" />
          {{ store.isConnected ? '在线' : '连接中...' }}
        </div>
      </div>
    </div>
    <div class="header-actions">
      <button class="icon-btn" @click="send('reload')" title="重载聊天记录">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
      </button>
      <button class="icon-btn" @click="send('clear')" title="清空对话">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14"/></svg>
      </button>
    </div>
  </header>
</template>

<style scoped>
.header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:14px 20px;
  border-bottom:1px solid var(--border);
  flex-shrink:0;
  background:var(--bg-secondary);
}

.header-left{
  display:flex;
  align-items:center;
  gap:12px;
}

.avatar-ring{
  width:44px;
  height:44px;
  border-radius:50%;
  padding:2px;
  background:linear-gradient(135deg,var(--text-muted),var(--bg-hover));
  transition:background .4s;
}

.avatar-ring.connected{
  background:linear-gradient(135deg,var(--accent),#a78bfa);
}

.avatar{
  width:40px;height:40px;border-radius:50%;object-fit:cover;display:block;
  border:2px solid var(--bg-secondary);
}

.header-name{
  font-size:15px;font-weight:600;color:var(--text-primary);
  display:flex;align-items:center;gap:4px;
}

.verified{
  font-size:10px;color:var(--accent);
  width:16px;height:16px;display:inline-flex;
  align-items:center;justify-content:center;
  background:var(--accent-glow);border-radius:50%;
}

.header-status{
  font-size:12px;color:var(--text-muted);margin-top:2px;
  display:flex;align-items:center;gap:6px;
}

.status-dot{
  width:7px;height:7px;border-radius:50%;background:var(--text-muted);
}

.status-dot.online{
  background:var(--success);
  box-shadow:0 0 6px var(--success);
}

.header-actions{
  display:flex;gap:4px;
}

.icon-btn{
  width:34px;height:34px;border:none;border-radius:var(--radius-sm);
  background:transparent;color:var(--text-muted);
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all .15s;
}

.icon-btn:hover{
  background:var(--bg-tertiary);
  color:var(--text-primary);
}
</style>
