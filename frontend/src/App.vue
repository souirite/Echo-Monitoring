<template>
  <div class="app">
    <div class="menu">
      <button @click="setView('faults')" :class="{ active: view === 'faults' }">Actual Faults</button>
      <button @click="setView('records')" :class="{ active: view === 'records' }">Records</button>
    </div>
    <div class="content">
      <Faults v-if="view === 'faults'" />
      <records v-if="view === 'records'" />
    </div>
  </div>
</template>

<script>
import Faults from './components/Faults.vue';
import Records from './components/Records.vue';

export default {
  components: { Faults,Records },
  data() {
    return {
      view: 'faults'
    };
  },
  methods: {
    setView(view) {
      this.view = view;
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
.content {
  flex: 1;
  padding: 20px;
}
</style>