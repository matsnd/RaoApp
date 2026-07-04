<script setup lang="ts">
/**
 * RAO-P3-071 Faza 5: Glossary tooltip dla skrotow w formularzach.
 *
 * Renderuje ikone "?" z tooltipem wyjasniajacym skrot (PNA, ZO, FA, OID, S/U).
 * Dostepny klawiatura (focus-visible pokazuje tooltip), respektuje hover.
 *
 * RAO-P3-071 kontynuacja: dodane props `description` (druga linia tooltipa),
 * `placement` ('top'|'bottom') oraz `size` (12|14|16 px). Dodatkowo:
 *  - `aria-expanded` reactive (ref<boolean> + @focus/@blur/@mouseenter/@mouseleave)
 *  - `@keydown.enter.prevent` / `@keydown.space.prevent` (role="button" wymaga)
 *
 * @example
 *   <GlossaryTip term="PNA" definition="Pocztowy Numer Adresowy" />
 *   <GlossaryTip
 *     term="OID"
 *     definition="Object ID — identyfikator umowy w Fakturownia"
 *     description="Domyślnie = numer umowy. Używany do synchronizacji faktur."
 *     placement="top"
 *     :size="12"
 *   />
 */
import { ref } from 'vue'

interface Props {
  /** Skrot wyswietlany w tooltipie jako <strong> (np. "PNA") */
  term: string
  /** Pelna nazwa — glowna tresc tooltipa (np. "Pocztowy Numer Adresowy") */
  definition: string
  /** Krotki opis 1-2 zdania — druga linia tooltipa (opcjonalny) */
  description?: string
  /** Pozycja tooltipa wzgledem triggera — domyslnie 'top' */
  placement?: 'top' | 'bottom'
  /** Rozmiar ikony triggera w px — domyslnie 16 */
  size?: 12 | 14 | 16
}

const props = withDefaults(defineProps<Props>(), {
  description: undefined,
  placement: 'top',
  size: 16,
})

/** aria-expanded — true gdy tooltip widoczny (focus lub hover) */
const expanded = ref(false)

function show(): void {
  expanded.value = true
}
function hide(): void {
  expanded.value = false
}
/** role="button" wymaga aktywacji klawiszem — toggle bez akcji (tooltip juz widoczny przez :focus-visible) */
function onActivate(): void {
  expanded.value = !expanded.value
}
</script>

<template>
  <span
    class="glossary-tip"
    :class="[`glossary-tip--${props.placement}`, `glossary-tip--${props.size}`]"
    tabindex="0"
    role="button"
    :aria-expanded="expanded"
    :aria-label="`${term}: ${definition}${description ? ' — ' + description : ''}`"
    :title="`${term}: ${definition}${description ? ' — ' + description : ''}`"
    @focus="show"
    @blur="hide"
    @mouseenter="show"
    @mouseleave="hide"
    @keydown.enter.prevent="onActivate"
    @keydown.space.prevent="onActivate"
  >
    <span aria-hidden="true">?</span>
    <span class="glossary-tip-text" role="tooltip">
      <strong>{{ term }}</strong> — {{ definition }}
      <span v-if="description" class="glossary-tip-desc">{{ description }}</span>
    </span>
  </span>
</template>
