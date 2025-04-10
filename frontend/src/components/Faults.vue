<template>
  <div>
    <h2>Actual Faults</h2>
    <table v-if="faults.length">
      <thead>
        <tr>
          <th>Bit Position</th>  <!-- New column for DBxxxx.DBXxx.x -->
          <th>Description</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="fault in faults" :key="fault.position">
          <td>{{ fault.position }}</td>  <!-- Display bit position -->
          <td>{{ fault.description }}</td>
          <td>{{ fault.state ? 'Active' : 'Inactive' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>No active faults</p>
  </div>
</template>

<script>
export default {
  name: 'Faults',
  data() {
    return {
      faults: [],
      ws: null
    };
  },
  mounted() {
    this.connectWebSocket();
  },
  beforeUnmount() {
    if (this.ws) this.ws.close();
  },
  methods: {
    connectWebSocket() {
      this.ws = new WebSocket('ws://localhost:8000/ws/bits');
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'plc_update') {
          this.faults = data.data.filter(fault => fault.state); // Show only active faults
        }
      };
      this.ws.onclose = () => console.log('WebSocket closed');
      this.ws.onerror = (error) => console.error('WebSocket error:', error);
    }
  }
};
</script>

<style>
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background: #f0f0f0; }
</style>