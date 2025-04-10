<template>
  <div>
    <h2>Records</h2>
    <table v-if="records.length">
      <thead>
        <tr>
          <th>Bit Position</th>  <!-- New column for DBxxxx.DBXxx.x -->
          <th>Description</th>
          <th>Start Time</th>
          <th>End Time</th>
          <th>Duration (s)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="record in records" :key="record.id">
          <td>{{ record.bit_position }}</td>  <!-- Display bit position -->
          <td>{{ record.description }}</td>
          <td>{{ record.start_time }}</td>
          <td>{{ record.end_time }}</td>
          <td>{{ record.duration }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>{{ error || 'No records found' }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Records',
  data() {
    return {
      records: [],
      error: null
    };
  },
  mounted() {
    console.log('Records component mounted');
    this.fetchRecords();
  },
  methods: {
    async fetchRecords() {
      try {
        console.log('Fetching records from http://localhost:8000/records');
        const response = await axios.get('http://localhost:8000/records');
        console.log('Records data:', response.data);
        if (response.data.error) {
          this.error = response.data.error;
          this.records = [];
        } else {
          this.records = Array.isArray(response.data) ? response.data : [];
          this.error = null;
        }
      } catch (error) {
        console.error('Error fetching records:', error);
        this.error = error.response?.data?.error || 'Failed to fetch records';
        this.records = [];
      }
    }
  }
};
</script>

<style>
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background: #f0f0f0; }
</style>