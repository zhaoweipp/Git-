<template>
  <div>
    <h2>Serial Transparent Bridge</h2>
    <textarea v-model="input" rows="4" cols="60" placeholder="输入要发送的内容"></textarea>
    <br />
    <button @click="send">发送到串口</button>
    <h3>日志</h3>
    <pre>{{ logs.join('\n') }}</pre>
  </div>
</template>

<script>
import { io } from 'socket.io-client'

export default {
  data() {
    return {
      socket: null,
      input: '',
      logs: []
    }
  },
  created() {
    this.connectSocket()
  },
  methods: {
    connectSocket() {
      this.socket = io('http://localhost:8000', {
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        timeout: 5000
      })

      this.socket.on('connect', () => this.logs.push('socket connected'))
      this.socket.on('disconnect', () => this.logs.push('socket disconnected'))
      this.socket.on('connect_error', e => this.logs.push('connect_error: ' + e.message))

      this.socket.on('serial_to_frontend', (msg) => {
        const raw = atob(msg.payload_b64)
        this.logs.push('serial recv: ' + raw)
      })

      this.socket.on('ack', (msg) => {
        this.logs.push('ack: ' + JSON.stringify(msg))
      })

      setInterval(() => {
        if (this.socket && this.socket.connected) {
          this.socket.emit('heartbeat', { ts: Date.now() })
        }
      }, 10000)
    },
    send() {
      const traceId = `${Date.now()}-${Math.random().toString(16).slice(2)}`
      const payload = btoa(this.input)
      this.socket.emit('frontend_to_serial', {
        trace_id: traceId,
        client_id: 'demo-client-001',
        payload_b64: payload
      })
      this.logs.push('send: ' + this.input)
    }
  }
}
</script>
