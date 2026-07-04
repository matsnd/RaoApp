<script setup lang="ts">
// RAO-P2-065 #16: lekki komponent ikon SVG (zamiast emoji).
// Bez zaleznosci zewnetrznych (lucide-vue-next niedostepny offline).
// Zestaw: tractor, map-pin, mail, trophy, building, dollar, file, chart,
//         calendar, search, wrench, package, layers.
// Kazda ikona: stroke=currentColor, 24x24 viewBox, stroke-width 2 (lucide-style).

export type AppIconName =
  | 'tractor'
  | 'map-pin'
  | 'mail'
  | 'trophy'
  | 'building'
  | 'dollar'
  | 'file'
  | 'chart'
  | 'calendar'
  | 'search'
  | 'wrench'
  | 'package'
  | 'layers'
  | 'check-circle'

interface Props {
  name: AppIconName
  size?: number | string
  title?: string
}

withDefaults(defineProps<Props>(), {
  size: 18,
  title: '',
})
</script>

<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :role="title ? 'img' : 'presentation'"
    :aria-label="title || undefined"
    :aria-hidden="title ? undefined : true"
  >
    <title v-if="title">{{ title }}</title>

    <template v-if="name === 'tractor'">
      <circle cx="7" cy="18" r="2.5" />
      <circle cx="17" cy="18" r="2.5" />
      <path d="M7 18h10" />
      <path d="M9 18V9h6l3 4v5" />
      <path d="M9 9V6h4" />
    </template>

    <template v-else-if="name === 'map-pin'">
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
      <circle cx="12" cy="10" r="3" />
    </template>

    <template v-else-if="name === 'mail'">
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </template>

    <template v-else-if="name === 'trophy'">
      <path d="M6 4h12v4a6 6 0 0 1-12 0Z" />
      <path d="M6 6H4a2 2 0 0 0 0 4h2" />
      <path d="M18 6h2a2 2 0 0 1 0 4h-2" />
      <path d="M12 14v4" />
      <path d="M9 20h6" />
    </template>

    <template v-else-if="name === 'building'">
      <rect x="4" y="3" width="16" height="18" rx="1" />
      <path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2" />
      <path d="M10 21v-3h4v3" />
    </template>

    <template v-else-if="name === 'dollar'">
      <line x1="12" y1="2" x2="12" y2="22" />
      <path d="M17 6.5C17 5 15 4 12 4S7 5 7 7s2 3 5 3 5 1 5 3-2 3-5 3-5-1-5-2.5" />
    </template>

    <template v-else-if="name === 'file'">
      <path d="M14 3v5h5" />
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M9 13h6M9 17h6" />
    </template>

    <template v-else-if="name === 'chart'">
      <path d="M3 3v18h18" />
      <path d="m7 14 4-4 3 3 5-6" />
    </template>

    <template v-else-if="name === 'calendar'">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </template>

    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </template>

    <template v-else-if="name === 'wrench'">
      <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18v3h3l6.3-6.3a4 4 0 0 0 5.4-5.4l-2.7 2.7-2-2Z" />
    </template>

    <template v-else-if="name === 'package'">
      <path d="m7.5 4.27 9 5.15" />
      <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
      <path d="m3.3 7 8.7 5 8.7-5M12 22V12" />
    </template>

    <template v-else-if="name === 'layers'">
      <path d="m12 2 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5" />
      <path d="m3 17 9 5 9-5" />
    </template>

    <!-- check-circle -->
    <template v-else-if="name === 'check-circle'">
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </template>
  </svg>
</template>

<style scoped>
.app-icon {
  display: inline-block;
  vertical-align: middle;
  flex: 0 0 auto;
}
</style>