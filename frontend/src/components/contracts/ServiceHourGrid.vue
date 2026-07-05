<template>
  <div class="service-hour-grid" data-testid="service-hour-grid">
    <div class="cond-header">
      <span class="cond-title">Ewidencja godzin operatora</span>
      <button class="btn btn-primary btn-sm" @click="addHour">+ Dodaj wpis</button>
    </div>
    <table class="data-grid" v-if="hours.length">
      <thead>
        <tr>
          <th style="width:130px;">Data</th>
          <th style="width:80px;">Od</th>
          <th style="width:80px;">Do</th>
          <th>Uwagi</th>
          <th style="width:80px;"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="hour in hours" :key="hour.id">
          <td>
            <input
              type="date"
              v-model="hour.service_date"
              class="form-control form-control-sm"
              @change="updateHour(hour)"
              data-testid="service-date-input"
            />
          </td>
          <td>
            <input
              type="time"
              v-model="hour.time_from"
              class="form-control form-control-sm"
              @change="updateHour(hour)"
              data-testid="time-from-input"
            />
          </td>
          <td>
            <input
              type="time"
              v-model="hour.time_to"
              class="form-control form-control-sm"
              @change="updateHour(hour)"
              data-testid="time-to-input"
            />
          </td>
          <td>
            <input
              type="text"
              v-model="hour.notes"
              class="form-control form-control-sm"
              placeholder="Uwagi"
              @change="updateHour(hour)"
              data-testid="notes-input"
            />
          </td>
          <td>
            <button class="btn-icon" title="Usuń" @click="removeHour(hour)" data-testid="remove-hour-btn">✕</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state" style="padding:16px;">Brak wpisów godzin — dodaj wpis</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useServiceHourStore } from '@/stores/serviceHours'

const props = defineProps({
  positionId: {
    type: Number,
    required: true
  }
})

const serviceHourStore = useServiceHourStore()
const hours = ref([])

async function loadHours() {
  hours.value = await serviceHourStore.fetchByPosition(props.positionId)
}

async function addHour() {
  const today = new Date().toISOString().split('T')[0]
  const newHour = await serviceHourStore.create(props.positionId, {
    service_date: today,
    time_from: null,
    time_to: null,
    notes: ''
  })
  hours.value.push(newHour)
}

async function updateHour(hour) {
  await serviceHourStore.update(props.positionId, hour.id, {
    service_date: hour.service_date,
    time_from: hour.time_from,
    time_to: hour.time_to,
    notes: hour.notes
  })
}

async function removeHour(hour) {
  if (confirm('Czy na pewno usunąć ten wpis?')) {
    await serviceHourStore.remove(props.positionId, hour.id)
    hours.value = hours.value.filter(h => h.id !== hour.id)
  }
}

onMounted(() => {
  loadHours()
})

defineExpose({
  loadHours
})
</script>

<style scoped>
.service-hour-grid {
  margin: 16px 0;
}

.cond-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.cond-title {
  font-weight: 600;
  color: var(--color-primary);
  font-size: 14px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #5A6B7E;
  padding: 4px;
}

.btn-icon:hover {
  color: #e53e3e;
}

.form-control-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.empty-state {
  color: #5A6B7E;
  font-style: italic;
  font-size: 13px;
}
</style>