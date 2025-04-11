<template>
  <div class="app">
    <div class="menu">
      <button
        v-for="station in 11"
        :key="'station-' + station"
        :class="{ 'station-button': true, 'no-faults': !hasFaults(station), 'has-faults': hasFaults(station), 'selected': selectedStation === station }"
        @click="selectStation(station)"
      >
        Station {{ station }}
      </button>
      <button @click="setView('faults')" :class="{ active: view === 'faults' }">Actual Faults</button>
      <button @click="setView('records')" :class="{ active: view === 'records' }">Records</button>
    </div>
    <div class="content">
      <Faults v-if="view === 'faults'" :selected-station="selectedStation" @faults-updated="updateFaults" />
      <Records v-if="view === 'records'" />
    </div>
  </div>
</template>
<script>
import Faults from './components/Faults.vue';
import Records from './components/Records.vue';

export default {
  components: { Faults, Records },
  data() {
    return {
      view: 'faults',
      selectedStation: 1,
      stationFaults: {}
    };
  },
  methods: {
    setView(view) {
      this.view = view;
    },
    selectStation(station) {
      this.selectedStation = station;
    },
    updateFaults(faults) {
      console.log('Faults received in App.vue:', faults);
      this.stationFaults = {};
      faults.forEach(fault => {
        const station = this.getStationNumber(fault.position);
        if (station !== -1) {  // Skip invalid stations
          if (!this.stationFaults[station]) {
            this.stationFaults[station] = [];
          }
          this.stationFaults[station].push(fault);
        }
      });
      console.log('Updated stationFaults:', this.stationFaults);
    },
    hasFaults(station) {
      return this.stationFaults[station] && this.stationFaults[station].length > 0;
    },
    getStationNumber(position) {
      if (!position || typeof position !== 'string' || !position.match(/DB\d+\.DBX/)) {
        console.warn('Invalid position in App.vue:', position);
        return -1;
      }
      const dbNumber = parseInt(position.match(/DB(\d+)\.DBX/)[1], 10);
      return Math.floor((dbNumber - 1020) / 1000) + 1;
    }
  }
};
</script>
<style>
.app {
  display: flex;
  height: 100vh;
}
.menu {
  width: 200px;
  background: #f0f0f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.menu button {
  padding: 10px;
  cursor: pointer;
}
.menu button.active {
  background: #007bff;
  color: white;
}
.station-button {
  border: none;
  border-radius: 5px;
  font-weight: bold;
}
.no-faults {
  background: #28a745; /* Green */
  color: white;
}
.has-faults {
  background: #dc3545; /* Red */
  color: white;
}
.selected {
  border: 2px solid #000; /* Highlight selected station */
}
.content {
  flex: 1;
  padding: 20px;
}
</style>