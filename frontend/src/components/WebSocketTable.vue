<template>
    <div class="websocket-table">
      <h2>Real-time Table Data via WebSocket</h2>
      
      <div class="connection-status" :class="connectionStatus">
        Status: {{ connectionStatus }}
        <button v-if="connectionStatus === 'disconnected'" @click="connect">Reconnect</button>
      </div>
      
      <div class="controls">
        <button @click="requestData">Request Latest Data</button>
      </div>
      
      <div class="last-update">
        Last update: {{ lastUpdate || 'Not received yet' }}
      </div>
      
      <table v-if="tableData.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Value</th>
            <th>Status</th>
            <th>Last Updated</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in tableData" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.value }}</td>
            <td :class="item.status">{{ item.status }}</td>
            <td>{{ item.last_updated }}</td>
          </tr>
        </tbody>
      </table>
      
      <div v-else class="no-data">
        No data received yet...
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, onBeforeUnmount } from 'vue'
  
  export default {
    setup() {
      const connectionStatus = ref('disconnected')
      const tableData = ref([])
      const lastUpdate = ref('')
      let socket = null
  
      const connect = () => {
        connectionStatus.value = 'connecting'
        socket = new WebSocket('ws://localhost:8000/ws')
  
        socket.onopen = () => {
          connectionStatus.value = 'connected'
          console.log('WebSocket connected')
        }
  
        socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            
            if (message.type === 'table_update') {
              tableData.value = message.data.data
              lastUpdate.value = message.data.timestamp
            } else if (message.type === 'error') {
              console.error('Server error:', message.message)
            }
          } catch (e) {
            console.error('Error parsing message:', e)
          }
        }
  
        socket.onerror = (error) => {
          console.error('WebSocket error:', error)
          connectionStatus.value = 'error'
        }
  
        socket.onclose = () => {
          connectionStatus.value = 'disconnected'
          console.log('WebSocket disconnected')
        }
      }
  
      const requestData = () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: 'request_data'
          }))
        }
      }
  
      onMounted(() => {
        connect()
      })
  
      onBeforeUnmount(() => {
        if (socket) {
          socket.close()
        }
      })
  
      return {
        connectionStatus,
        tableData,
        lastUpdate,
        connect,
        requestData
      }
    }
  }
  </script>
  
  <style scoped>
  .websocket-table {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .connection-status {
    padding: 10px;
    margin-bottom: 20px;
    border-radius: 4px;
  }
  
  .connection-status.connected {
    background-color: #d4edda;
    color: #155724;
  }
  
  .connection-status.disconnected,
  .connection-status.error {
    background-color: #f8d7da;
    color: #721c24;
  }
  
  .connection-status.connecting {
    background-color: #fff3cd;
    color: #856404;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
  }
  
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  
  th {
    background-color: #f2f2f2;
  }
  
  tr:nth-child(even) {
    background-color: #f9f9f9;
  }
  
  .active {
    color: green;
    font-weight: bold;
  }
  
  .inactive {
    color: red;
  }
  
  .pending {
    color: orange;
  }
  
  .controls {
    margin: 15px 0;
  }
  
  .last-update {
    font-style: italic;
    color: #666;
    margin-bottom: 10px;
  }
  
  .no-data {
    margin-top: 20px;
    padding: 20px;
    background-color: #f8f9fa;
    border: 1px dashed #ddd;
    text-align: center;
  }
  </style>