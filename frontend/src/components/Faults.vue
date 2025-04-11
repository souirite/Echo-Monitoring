<template>
  <div>
    <h2>Actual Faults - Station {{ selectedStation }}</h2>
    <table v-if="filteredFaults.length">
      <thead>
        <tr>
          <th>Bit Position</th>
          <th>Description</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="fault in filteredFaults" :key="fault.position">
          <td>{{ fault.position }}</td>
          <td>{{ fault.description }}</td>
          <td>{{ fault.state ? 'Active' : 'Inactive' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>No active faults for Station {{ selectedStation }}</p>
  </div>
</template>

<script>
export default {
  name: 'Faults',
  props: {
    selectedStation: { type: Number, default: 1 }
  },
  data() {
    return {
      faults: [],
      ws: null
    };
  },
  computed: {
    filteredFaults() {
      const filtered = this.faults.filter(fault => {
        const station = this.getStationNumber(fault.position);
        return station === this.selectedStation && fault.state;
      });
      console.log(`Filtered faults for Station ${this.selectedStation}:`, filtered);
      return filtered;
    }
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
        console.log('WebSocket data received:', data);
        if (data.type === 'plc_update' && Array.isArray(data.data)) {
          this.faults = data.data.filter(fault => fault && typeof fault.position === 'string' && fault.position.match(/DB\d+\.DBX/));
          console.log('All faults stored:', this.faults);
          this.$emit('faults-updated', this.faults.filter(fault => fault.state));
        }
      };
      this.ws.onopen = () => console.log('WebSocket connected');
      this.ws.onclose = () => console.log('WebSocket closed');
      this.ws.onerror = (error) => console.error('WebSocket error:', error);
    },
    getStationNumber(position) {
      if (!position || typeof position !== 'string' || !position.match(/DB\d+\.DBX/)) {
        console.warn('Invalid position in Faults.vue:', position);
        return -1;
      }
      const dbNumber = parseInt(position.match(/DB(\d+)\.DBX/)[1], 10);
      return Math.floor((dbNumber - 1020) / 1000) + 1;
    }
  }
};
</script>
<style>
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background: #f0f0f0; }
</style>