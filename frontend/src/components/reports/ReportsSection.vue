<template>
  <div class="reports-dashboard">

    <!-- TABS -->
    <div class="tabs-bar">
      <button :class="['tab', { 'tab-active': activeTab === 'live' }]" @click="switchTab('live')">
        <span class="tab-dot" :class="activeTab === 'live' ? 'tab-dot-active' : ''"></span>
        Stan floty teraz
      </button>
      <button :class="['tab', { 'tab-active': activeTab === 'history' }]" @click="switchTab('history')">
        📅 Analiza historyczna
      </button>
      <button :class="['tab', { 'tab-active': activeTab === 'explorer' }]" @click="switchTab('explorer')">
        🔍 Eksplorator
      </button>
    </div>

    <!-- ══════════════════ TAB: TERAZ ══════════════════ -->
    <div v-show="activeTab === 'live'">
      <!-- SECTION HEADER - wizualne wyodrębnienie -->
      <div class="current-status-header">
        <div class="current-status-title">📊 Stan aktualny floty</div>
        <div class="current-status-subtitle">Dane na dzień dzisiejszy — niezależne od filtrów datowych</div>
      </div>

      <div v-if="statsStore.loadingLive" class="reports-loading">
        <div class="spinner"></div>
        <span>Ładowanie stanu floty...</span>
      </div>
      <template v-else>
        <div class="kpi-row kpi-row-live" v-if="statsStore.currentlyRented">
          <div class="kpi-card">
            <div class="kpi-value kpi-success">{{ statsStore.currentlyRented.total_machines - statsStore.currentlyRented.total_rented }}</div>
            <div class="kpi-label">Dostępnych</div>
            <div class="kpi-sub">z {{ statsStore.currentlyRented.total_machines }} maszyn łącznie</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-value" :class="liveUtilClass">{{ liveUtilPct }}%</div>
            <div class="kpi-label">Wykorzystanie floty</div>
            <div class="kpi-sub">% maszyn u klientów teraz</div>
          </div>
          <div class="chart-panel" style="padding:16px 18px;">
            <div class="chart-title" style="margin-bottom:8px;">📊 Stan floty</div>
            <div class="chart-wrap" style="height:160px;">
              <canvas ref="donutCanvas"></canvas>
            </div>
          </div>
        </div>

        <div class="table-panel full-width" v-if="statsStore.currentlyRented?.items?.length">
          <div class="table-title">Maszyny aktualnie wynajęte</div>
          <div class="rented-scroll">
            <table class="stats-table" data-testid="live-rented-table">
              <thead>
                <tr>
                  <th>Maszyna</th>
                  <th>Nr wewnętrzny</th>
                  <th>Kategoria</th>
                  <th>Umowa</th>
                  <th>Kontrahent</th>
                  <th>Planowany zwrot</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in statsStore.currentlyRented.items" :key="item.article_id + item.contract_number">
                  <td>{{ item.name }}</td>
                  <td>{{ item.internal_number || '—' }}</td>
                  <td>{{ item.category_main || '—' }}</td>
                  <td style="font-weight:600;">{{ item.contract_number }}</td>
                  <td>{{ item.contractor_name || '—' }}</td>
                  <td>{{ item.return_date ? new Date(item.return_date).toLocaleDateString('pl-PL') : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else-if="statsStore.currentlyRented" class="empty-state">
          Brak aktywnych wynajmów
        </div>
      </template>
    </div>

    <!-- ══════════════════ TAB: HISTORIA ══════════════════ -->
    <div v-show="activeTab === 'history'">
      <!-- DATE PILLS -->
      <div class="date-pills">
        <button
          v-for="p in presets"
          :key="p.key"
          :class="['pill', { active: activePreset === p.key }]"
          @click="selectPreset(p.key)"
        >{{ p.label }}</button>
        <div class="pill-custom" v-if="activePreset === 'custom'">
          <input type="date" v-model="customFrom" class="pill-date" />
          <span>—</span>
          <input type="date" v-model="customTo" class="pill-date" />
          <button class="pill pill-go" @click="applyPeriodFilter()">Filtruj</button>
        </div>
        <button :class="['pill', { active: activePreset === 'custom' }]" @click="activePreset = 'custom'">📅 Własny</button>
        <button class="btn-print print-hide" @click="printPage">🖨 Drukuj</button>
      </div>

      <!-- RAO-P2-010: FILTR TYP POZYCJI -->
      <div class="position-type-filter" v-if="historySubTab === 'general'">
        <span class="filter-label">Typ pozycji:</span>
        <button :class="['pill', { active: positionType === 'all' }]" @click="positionType = 'all'">Wszystkie</button>
        <button :class="['pill', { active: positionType === 'machines' }]" @click="positionType = 'machines'">Maszyny</button>
        <button :class="['pill', { active: positionType === 'services' }]" @click="positionType = 'services'">Usługi</button>
      </div>

      <!-- RAO-P1-026: Shared filter panel for Kategorie + Historia sub-tabs -->
      <div class="shared-filter-bar" v-if="historySubTab === 'categories' || historySubTab === 'timeline'">
        <!-- Rodzaj -->
        <div class="filter-group" style="position:relative;">
          <span class="filter-label">Rodzaj:</span>
          <button :class="['pill', { active: sharedArticleType === 'all' }]" @click="setSharedArticleType('all')">Wszystkie</button>
          <button :class="['pill', { active: sharedArticleType === 'machine' }]" @click="setSharedArticleType('machine')">Maszyny</button>
          <button :class="['pill', { active: sharedArticleType === 'service' }]" @click="setSharedArticleType('service')">Usługi</button>
        </div>
        <!-- Kategoria główna (multi-select dropdown) -->
        <div class="filter-group shared-cat-dropdown" ref="catDropdownRef">
          <span class="filter-label">Kategoria:</span>
          <button class="pill dropdown-trigger" @click="catDropdownOpen = !catDropdownOpen">
            {{ sharedCategoryMains.length ? sharedCategoryMains.join(', ') : '— wszystkie —' }} ▾
          </button>
          <div class="dropdown-menu" v-if="catDropdownOpen">
            <label v-for="cat in statsStore.categoriesList" :key="cat.id" class="dropdown-item">
              <input type="checkbox" :value="cat.name" v-model="sharedCategoryMains" /> {{ cat.name }}
            </label>
            <button class="dropdown-clear" @click="sharedCategoryMains = []">✕ Wyczyść</button>
          </div>
        </div>
      </div>

      <!-- HISTORIA SUB-TABS -->
      <div class="explorer-subtabs" data-testid="history-subtabs">
        <button
          data-testid="history-subtab-general"
          :class="['subtab', { 'subtab-active': historySubTab === 'general' }]"
          @click="switchHistorySubTab('general')"
        >📊 Ogólne</button>
        <button
          data-testid="history-subtab-categories"
          :class="['subtab', { 'subtab-active': historySubTab === 'categories' }]"
          @click="switchHistorySubTab('categories')"
        >🏷️ Kategorie</button>
        <button
          data-testid="history-subtab-timeline"
          :class="['subtab', { 'subtab-active': historySubTab === 'timeline' }]"
          @click="switchHistorySubTab('timeline')"
        >📅 Historia</button>
      </div>

      <!-- SUB-TAB: Ogólne -->
      <div v-show="historySubTab === 'general'">
      <div v-if="statsStore.loading" class="reports-loading">
        <div class="spinner"></div>
        <span>Ładowanie statystyk...</span>
      </div>
      <template v-else>
        <div class="kpi-row" v-if="statsStore.summary" style="grid-template-columns: repeat(2, 1fr); max-width: 600px;">
          <div class="kpi-card">
            <div class="kpi-value">{{ formatMoney(statsStore.summary.period_revenue) }}</div>
            <div class="kpi-label">Przychód w okresie</div>
            <div class="kpi-sub">{{ statsStore.summary.contracts_in_period }} umów</div>
          </div>
          <div class="kpi-card kpi-highlight" v-if="statsStore.summary.top_machine_name">
            <div class="kpi-value kpi-small">{{ statsStore.summary.top_machine_name }}</div>
            <div class="kpi-label">Top maszyna</div>
            <div class="kpi-sub">{{ formatMoney(statsStore.summary.top_machine_revenue) }}</div>
          </div>
          <div class="kpi-card" v-else>
            <div class="kpi-value kpi-muted">—</div>
            <div class="kpi-label">Top maszyna</div>
            <div class="kpi-sub">brak danych</div>
          </div>
        </div>

        <div class="charts-row" style="grid-template-columns: 1fr;">
          <div class="chart-panel">
            <div class="chart-title">🏗️ TOP 10 Maszyn wg przychodu w okresie</div>
            <div class="chart-wrap" style="height:280px;">
              <canvas ref="barCanvas"></canvas>
            </div>
            <div v-if="!statsStore.topMachines.length" class="empty-state" style="padding:60px 0;text-align:center;">Brak danych w wybranym okresie</div>
          </div>
        </div>

        <div class="tables-row">
          <div class="table-panel">
            <div class="table-title">💰 Usługi dodatkowe w okresie</div>
            <table class="stats-table" v-if="statsStore.additionalFees?.breakdown?.length">
              <thead>
                <tr>
                  <th>Usługa</th>
                  <th style="text-align:right;">Przychód</th>
                  <th style="text-align:right;">Umów</th>
                  <th style="width:120px;"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in statsStore.additionalFees.breakdown" :key="s.article_id">
                  <td>{{ s.service_name }}</td>
                  <td style="text-align:right;font-weight:600;">{{ formatMoney(s.total_revenue) }}</td>
                  <td style="text-align:right;">{{ s.times_billed }}</td>
                  <td>
                    <div class="bar-bg">
                      <div class="bar-fill" :style="{ width: feeBarWidth(s.total_revenue) + '%' }"></div>
                    </div>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td style="font-weight:700;">Razem</td>
                  <td style="text-align:right;font-weight:700;">{{ formatMoney(statsStore.additionalFees.total_services_revenue) }}</td>
                  <td></td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
            <div v-else class="empty-state">Brak usług w wybranym okresie</div>
          </div>

          <div class="table-panel">
            <div class="table-title">📍 Lokalizacje — ranking w okresie</div>
            <table class="stats-table" v-if="statsStore.locations.length">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Miasto</th>
                  <th style="text-align:right;">Umów</th>
                  <th style="text-align:right;">Przychód</th>
                  <th style="width:100px;"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(loc, i) in statsStore.locations" :key="loc.city">
                  <td style="color:#718096;">{{ i + 1 }}</td>
                  <td style="font-weight:600;">{{ loc.city }}</td>
                  <td style="text-align:right;">{{ loc.rentals_count }}</td>
                  <td style="text-align:right;">{{ formatMoney(loc.total_revenue) }}</td>
                  <td>
                    <div class="bar-bg">
                      <div class="bar-fill bar-fill-blue" :style="{ width: locBarWidth(loc.rentals_count) + '%' }"></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state">Brak danych lokalizacji</div>
          </div>

          <!-- RAO-P2-010: Tabela pozycji z filtrem typu -->
          <div class="table-panel full-width" v-if="statsStore.positionsData">
            <div class="table-title">📋 Pozycje ({{ statsStore.positionsData.type === 'all' ? 'Wszystkie' : statsStore.positionsData.type === 'machines' ? 'Maszyny' : 'Usługi' }})</div>
            <table class="stats-table" v-if="statsStore.positionsData.items?.length">
              <thead>
                <tr>
                  <th>Nazwa</th>
                  <th>Nr wewnętrzny</th>
                  <th>Kategoria</th>
                  <th style="text-align:right;">Przychód</th>
                  <th style="text-align:right;">Dni</th>
                  <th style="text-align:right;">Umów</th>
                  <th style="text-align:right;">Razy</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pos in statsStore.positionsData.items" :key="pos.article_id">
                  <td style="font-weight:600;">{{ pos.article_name }}</td>
                  <td>{{ pos.internal_number || '—' }}</td>
                  <td>{{ pos.category_main || '—' }}</td>
                  <td style="text-align:right;font-weight:600;">{{ formatMoney(pos.revenue) }}</td>
                  <td style="text-align:right;">{{ pos.rented_days }}</td>
                  <td style="text-align:right;">{{ pos.contracts_count }}</td>
                  <td style="text-align:right;">{{ pos.times_billed }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="3" style="font-weight:700;">Suma</td>
                  <td style="text-align:right;font-weight:700;">{{ formatMoney(statsStore.positionsData.total_revenue) }}</td>
                  <td></td>
                  <td></td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
            <div v-else class="empty-state">Brak pozycji w wybranym okresie</div>
            <div class="positions-summary" v-if="statsStore.positionsData">
              <span>Maszyny: <strong>{{ formatMoney(statsStore.positionsData.total_machines_revenue) }}</strong></span>
              <span style="margin-left:16px;">Usługi: <strong>{{ formatMoney(statsStore.positionsData.total_services_revenue) }}</strong></span>
            </div>
          </div>
        </div>
      </template>
      </div><!-- /historySubTab === 'general' -->

      <!-- SUB-TAB: Kategorie (RAO-P1-017/026) -->
      <div v-show="historySubTab === 'categories'" data-testid="categories-panel">
        <!-- RAO-P2-021: Banner informacyjny o danych historycznych -->
        <div class="history-banner" data-testid="history-banner">
          ℹ️ Raporty kategorii zawierają dane historyczne zaimportowane z poprzedniej aplikacji.
          Archiwalne maszyny i umowy są uwzględnianie wyłącznie w statystykach historycznych.
        </div>

        <!-- Loading state -->
        <div v-if="statsStore.loadingByCategory" class="reports-loading">
          <div class="spinner"></div>
          <span>Ładowanie danych kategorii...</span>
        </div>

        <!-- Error state -->
        <div v-else-if="errorByCategory" class="category-error-state">
          ⚠️ {{ errorByCategory }}
        </div>

        <!-- Empty state -->
        <div v-else-if="!statsStore.byCategoryData?.items?.length" class="empty-state" style="padding:60px 0;text-align:center;">
          Brak danych dla wybranego okresu
        </div>

        <!-- Data -->
        <template v-else>
          <!-- Drilldown breadcrumb -->
          <div class="drilldown-breadcrumb" v-if="drilldownPath.length > 0">
            <span class="breadcrumb-item clickable" @click="drillTo(0)">Wszystkie</span>
            <template v-for="(segment, idx) in drilldownPath" :key="idx">
              <span class="breadcrumb-sep"> / </span>
              <span
                :class="['breadcrumb-item', { clickable: idx < drilldownPath.length - 1 }]"
                @click="idx < drilldownPath.length - 1 ? drillTo(idx + 1) : null"
              >{{ segment }}</span>
            </template>
          </div>

          <!-- KPI summary -->
          <div class="kpi-row" style="grid-template-columns: repeat(3, 1fr); max-width: 700px;">
            <div class="kpi-card">
              <div class="kpi-value kpi-small">{{ formatMoney(statsStore.byCategoryData.total_revenue) }}</div>
              <div class="kpi-label">Łączny przychód</div>
              <div class="kpi-sub">za wybrany okres</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-value">{{ statsStore.byCategoryData.items.length }}</div>
              <div class="kpi-label">Aktywnych kategorii</div>
              <div class="kpi-sub">z wynajmem w okresie</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-value">{{ totalCategoryDays }}</div>
              <div class="kpi-label">Dni wynajmu</div>
              <div class="kpi-sub">łącznie we wszystkich kategorii</div>
            </div>
          </div>

          <!-- Table -->
          <div class="table-panel full-width">
            <!-- Back button (nad tabelą) -->
            <button class="drillback-main-btn" v-if="drilldownPath.length > 0" @click="drillBack" title="Cofnij">
              ← Cofnij
            </button>
            <div class="table-title">📋 Zestawienie kategorii</div>
            <table class="stats-table" data-testid="category-stats-table">
              <thead>
                <tr>
                  <th style="cursor:pointer;" @click="toggleSort('category_name')">Kategoria{{ sortIcon('category_name') }}</th>
                  <th style="text-align:right;cursor:pointer;" @click="toggleSort('articles_count')">Maszyny{{ sortIcon('articles_count') }}</th>
                  <th style="text-align:right;cursor:pointer;" @click="toggleSort('rented_days')">Dni wynajmu{{ sortIcon('rented_days') }}</th>
                  <th style="text-align:right;cursor:pointer;" @click="toggleSort('contracts_count')">Umowy{{ sortIcon('contracts_count') }}</th>
                  <th style="text-align:right;cursor:pointer;" @click="toggleSort('revenue')">Przychód{{ sortIcon('revenue') }}</th>
                  <th style="width:130px;"></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="cat in sortedCategoryItems"
                  :key="cat.category_name"
                  :class="{ 'drilldown-row': categoryHasChildren(cat.category_name) }"
                  @click="categoryHasChildren(cat.category_name) ? drillDown(cat.category_name) : null"
                  :style="categoryHasChildren(cat.category_name) ? 'cursor:pointer' : ''"
                >
                  <td style="font-weight:600;">
                    {{ cat.category_name }}
                    <span v-if="categoryHasChildren(cat.category_name)" class="drilldown-arrow">›</span>
                  </td>
                  <td style="text-align:right;">{{ cat.articles_count }}</td>
                  <td style="text-align:right;">{{ cat.rented_days }}</td>
                  <td style="text-align:right;">{{ cat.contracts_count }}</td>
                  <td style="text-align:right;font-weight:600;">{{ formatMoney(cat.revenue) }}</td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Bar chart -->
          <div class="charts-row" style="grid-template-columns: 1fr;">
            <div class="chart-panel">
              <div class="chart-title">🏷️ Kategorie wg przychodu (TOP 15)</div>
              <div class="chart-wrap" style="height:280px;">
                <canvas data-testid="category-bar-chart" ref="categoryBarCanvas"></canvas>
              </div>
              <div v-if="!statsStore.byCategoryData.items.length" class="empty-state" style="padding:60px 0;text-align:center;">
                Brak danych w wybranym okresie
              </div>
            </div>
          </div>
        </template>
      </div><!-- /historySubTab === 'categories' -->

      <!-- SUB-TAB: Historia (RAO-P1-026) -->
      <div v-show="historySubTab === 'timeline'" data-testid="timeline-panel">

        <!-- Granularity toggle -->
        <div class="category-level-bar">
          <span class="period-label">Grupuj po:</span>
          <button :class="['pill', { active: granularity === 'month' }]" @click="setGranularity('month')">Miesiące</button>
          <button :class="['pill', { active: granularity === 'year' }]" @click="setGranularity('year')">Lata</button>
        </div>

        <!-- Loading -->
        <div v-if="statsStore.loadingByPeriod" class="reports-loading">
          <div class="spinner"></div>
          <span>Ładowanie danych historii...</span>
        </div>

        <!-- Error -->
        <div v-else-if="errorByPeriod" class="category-error-state">
          ⚠️ {{ errorByPeriod }} <button class="btn-link" @click="loadPeriodData">Spróbuj ponownie</button>
        </div>

        <!-- Empty -->
        <div v-else-if="!statsStore.byPeriodData?.items?.length" class="empty-state" style="padding:60px 0;text-align:center;">
          Brak danych dla wybranych filtrów
        </div>

        <!-- Data -->
        <template v-else>
          <!-- Chart -->
          <div class="charts-row" style="grid-template-columns: 1fr;">
            <div class="chart-panel">
              <div class="chart-title">📅 Przychód per {{ granularity === 'month' ? 'miesiąc' : 'rok' }}</div>
              <div class="chart-wrap" style="height:280px;">
                <canvas ref="periodBarCanvas"></canvas>
              </div>
            </div>
          </div>

          <!-- Pivot table -->
          <div class="table-panel full-width" v-if="pivotData">
            <div class="table-title">📋 Tabela przestawna — przychód per {{ granularity === 'month' ? 'miesiąc' : 'rok' }}</div>
            <div style="overflow-x:auto;">
              <table class="stats-table pivot-table">
                <thead>
                  <tr>
                    <th>Kategoria</th>
                    <th v-for="period in pivotData.periods" :key="period" style="text-align:right;min-width:80px;">
                      {{ formatPeriod(period) }}
                    </th>
                    <th style="text-align:right;font-weight:700;">SUMA</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in pivotData.rows" :key="row.category">
                    <td style="font-weight:600;cursor:pointer;" @click="selectPivotCategory(row.category)">{{ row.category }}</td>
                    <td v-for="period in pivotData.periods" :key="period" style="text-align:right;">
                      {{ formatMoney(row.values[period] || 0) }}
                    </td>
                    <td style="text-align:right;font-weight:700;">{{ formatMoney(row.total) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr style="font-weight:700;border-top:2px solid var(--color-border, #e0e0e0);">
                    <td>SUMA</td>
                    <td v-for="period in pivotData.periods" :key="period" style="text-align:right;">
                      {{ formatMoney(pivotData.totals[period] || 0) }}
                    </td>
                    <td style="text-align:right;">{{ formatMoney(pivotData.grandTotal) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </template>
      </div><!-- /historySubTab === 'timeline' -->
    </div>

    <!-- ══════════════════ TAB: EKSPERATOR ══════════════════ -->
    <div v-show="activeTab === 'explorer'">
      <!-- SUB-TABS -->
      <div class="explorer-subtabs">
        <button :class="['subtab', { 'subtab-active': explorerTab === 'all' }]" @click="switchExplorerTab('all')">
          🔍 Wszystko
        </button>
        <button :class="['subtab', { 'subtab-active': explorerTab === 'machines' }]" @click="switchExplorerTab('machines')">
          🏗️ Maszyny
        </button>
        <button :class="['subtab', { 'subtab-active': explorerTab === 'services' }]" @click="switchExplorerTab('services')">
          🛠️ Usługi
        </button>
        <button :class="['subtab', { 'subtab-active': explorerTab === 'locations' }]" @click="switchExplorerTab('locations')">
          📍 Lokalizacje
        </button>
      </div>

      <!-- PERIOD PILLS -->
      <div class="explorer-period-bar">
        <label class="period-label">Okres:</label>
        <button v-for="p in explorerPresets" :key="p.key"
          :class="['pill', { active: explorerPeriod === p.key }]"
          @click="setExplorerPeriod(p.key)">{{ p.label }}</button>
        <button :class="['pill', { active: explorerPeriod === 'custom' }]" @click="setExplorerPeriod('custom')">📅 Własny</button>
        <div v-if="explorerPeriod === 'custom'" class="pill-custom">
          <input type="date" v-model="explorerCustomFrom" class="pill-date" />
          <span>—</span>
          <input type="date" v-model="explorerCustomTo" class="pill-date" />
          <button class="pill pill-go" @click="onExplorerPeriodChange">Filtruj</button>
        </div>
      </div>

      <!-- SEARCH (only for Wszystko tab) -->
      <div v-if="explorerTab === 'all'" class="explorer-filters">
        <div class="filter-group">
          <label>Szukaj:</label>
          <input v-model="explorerQuery" type="text" placeholder="Maszyna, nr wewnętrzny, kontrahent..." class="explorer-search" @keyup.enter="searchExplorer" />
          <button class="pill pill-go" @click="searchExplorer" :disabled="loadingExplorer">
            {{ loadingExplorer ? 'Szukanie...' : 'Szukaj' }}
          </button>
        </div>
      </div>

      <!-- LOADING -->
      <div v-if="loadingExplorer" class="reports-loading">
        <div class="spinner"></div>
        <span>Ładowanie wyników...</span>
      </div>

      <!-- RESULTS -->
      <template v-else>
        <!-- TAB: Wszystko -->
        <div v-show="explorerTab === 'all'">
          <div class="table-panel full-width">
            <div class="table-title">Wyniki wyszukiwania ({{ explorerResults.length }})</div>
            <table class="stats-table" v-if="explorerResults.length">
              <thead>
                <tr>
                  <th>Typ</th>
                  <th>Nazwa</th>
                  <th>Nr wewn.</th>
                  <th>Kontrahent</th>
                  <th>Data</th>
                  <th style="text-align:right;">Kwota</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in explorerResults" :key="item.id" @click="openExplorerItem(item)" class="row-clickable">
                  <td>{{ item.type }} {{ item.type_label }}</td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.internal_number || '—' }}</td>
                  <td>{{ item.contractor_name || '—' }}</td>
                  <td>{{ item.date ? new Date(item.date).toLocaleDateString('pl-PL') : '—' }}</td>
                  <td style="text-align:right;font-weight:600;">{{ formatMoney(item.amount) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state">Wpisz frazę i kliknij "Szukaj"</div>
          </div>
          <div v-if="explorerSummary.count" class="explorer-summary">
            Podsumowanie: <strong>{{ explorerSummary.count }}</strong> wyników | 
            Przychód: <strong>{{ formatMoney(explorerSummary.revenue) }}</strong>
          </div>
        </div>

        <!-- TAB: Maszyny -->
        <div v-show="explorerTab === 'machines'">
          <div class="explorer-machine-selector">
            <label>Szukaj maszynę:</label>
            <input v-model="machineSearch" type="text" placeholder="Wpisz nazwę lub nr wewnętrzny..." class="explorer-search" style="width:320px;" @input="onMachineSearchInput" @keyup.enter="pickFirstMachine" />
            <span v-if="loadingExplorer" class="search-hint">Szukanie...</span>
          </div>
          <div v-if="machineSearchResults.length && !machineDetails" class="machine-search-results">
            <div v-for="m in machineSearchResults" :key="m.id" class="machine-result-row" @click="pickMachine(m.id)">
              <span class="machine-result-name">{{ m.name }}</span>
              <span v-if="m.internal_number" class="machine-result-nr">[{{ m.internal_number }}]</span>
            </div>
          </div>
          <div v-if="machineDetails" class="machine-metrics">
            <button class="machine-back-btn" @click="machineDetails = null; machineSearch = ''; selectedMachine = ''">← Szukaj inną maszynę</button>
            <div class="metrics-header">
              <h3>📊 {{ machineDetails.machine.name }}</h3>
              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-value">{{ formatMoney(machineDetails.metrics.total_revenue) }}</div>
                  <div class="metric-label">Przychód</div>
                </div>
                <div class="metric-card">
                  <div class="metric-value">{{ machineDetails.metrics.total_days }} dni</div>
                  <div class="metric-label">Wynajmu</div>
                </div>
                <div class="metric-card">
                  <div class="metric-value">{{ formatMoney(machineDetails.metrics.avg_daily_revenue) }}</div>
                  <div class="metric-label">Średnio/dzień</div>
                </div>
                <div class="metric-card" v-if="machineDetails.metrics.utilization_percentage">
                  <div class="metric-value">{{ machineDetails.metrics.utilization_percentage }}%</div>
                  <div class="metric-label">Wykorzystanie</div>
                </div>
              </div>
            </div>
            <div class="table-panel">
              <div class="table-title">Historia wynajmów ({{ machineDetails.rentals.length }})</div>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Umowa</th>
                    <th>Kontrahent</th>
                    <th>Od</th>
                    <th>Do</th>
                    <th>Dni</th>
                    <th style="text-align:right;">Kwota</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in machineDetails.rentals" :key="r.contract_id">
                    <td>{{ r.contract_number }}</td>
                    <td>{{ r.contractor_name }}</td>
                    <td>{{ r.date_from ? new Date(r.date_from).toLocaleDateString('pl-PL') : '—' }}</td>
                    <td>{{ r.date_to ? new Date(r.date_to).toLocaleDateString('pl-PL') : '—' }}</td>
                    <td>{{ r.days }}</td>
                    <td style="text-align:right;font-weight:600;">{{ formatMoney(r.revenue) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- TAB: Usługi -->
        <div v-show="explorerTab === 'services'">
          <!-- Detail panel -->
          <div v-if="serviceDetails" class="detail-panel">
            <button class="machine-back-btn" @click="serviceDetails = null">&#8592; Wroc</button>
            <div class="metrics-header">
              <h3>&#128296; {{ serviceDetails.service.name }}</h3>
              <div class="period-info">&#128197; Okres: {{ getExplorerPeriodLabel() }}</div>
              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-value">{{ serviceDetails.metrics.times_billed }}</div>
                  <div class="metric-label">Razy rozliczone</div>
                </div>
                <div class="metric-card">
                  <div class="metric-value">{{ formatMoney(serviceDetails.metrics.total_revenue) }}</div>
                  <div class="metric-label">Przychod</div>
                </div>
              </div>
            </div>
            <div class="table-panel" v-if="serviceDetails.top_contractors?.length">
              <div class="table-title">&#127942; Top kontrahenci</div>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Kontrahent</th>
                    <th style="text-align:right;">Umow</th>
                    <th style="text-align:right;">Przychod</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in serviceDetails.top_contractors" :key="c.contractor_name">
                    <td>{{ c.contractor_name }}</td>
                    <td style="text-align:right;">{{ c.contract_count }}</td>
                    <td style="text-align:right;font-weight:600;">{{ formatMoney(c.total_revenue) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="table-panel" v-if="serviceDetails.location_breakdown?.length">
              <div class="table-title">&#128205; Lokalizacje</div>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Miasto</th>
                    <th style="text-align:right;">Umow</th>
                    <th style="text-align:right;">Przychod</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="loc in serviceDetails.location_breakdown" :key="loc.city">
                    <td>{{ loc.city }}</td>
                    <td style="text-align:right;">{{ loc.contract_count }}</td>
                    <td style="text-align:right;font-weight:600;">{{ formatMoney(loc.total_revenue) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <!-- List view -->
          <div v-else>
            <div class="service-filters">
              <button :class="['service-chip', { active: selectedService === '' }]" @click="filterService('')">
                Wszystkie
              </button>
              <button v-for="g in serviceGroups" :key="g.key"
                :class="['service-chip', { active: selectedService === g.key }]"
                @click="filterService(g.key)">
                {{ g.label }} <span class="chip-count">{{ g.count }}</span>
              </button>
            </div>
            <div class="explorer-machine-selector" style="margin-top: 16px;">
              <label>Szukaj usługę:</label>
              <input v-model="serviceSearch" type="text" placeholder="Wpisz nazwę usługi..." class="explorer-search" style="width:320px;" @input="onServiceSearchInput" />
              <div v-if="serviceSearchResults.length" class="machine-search-results">
                <div v-for="s in serviceSearchResults" :key="s.article_id" class="machine-result-row" @click="pickService(s.article_id)">
                  <span class="machine-result-name">{{ s.service_name }}</span>
                  <span class="machine-result-nr">{{ s.times_billed }} razy</span>
                </div>
              </div>
            </div>
            <div class="table-panel full-width">
              <div class="table-title">Podsumowanie uslug</div>
              <table class="stats-table" v-if="filteredServices.length">
                <thead>
                  <tr>
                    <th>Usluga</th>
                    <th style="text-align:right;">Ilosc</th>
                    <th style="text-align:right;">Przychod</th>
                    <th style="text-align:right;">%</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in filteredServices" :key="s.article_id" @click="openServiceDetails(s)" class="row-clickable">
                    <td>{{ s.service_name }}</td>
                    <td style="text-align:right;">{{ s.times_billed }}</td>
                    <td style="text-align:right;font-weight:600;">{{ formatMoney(s.total_revenue) }}</td>
                    <td style="text-align:right;">{{ s.percentage }}%</td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="empty-state">Brak danych uslug</div>
            </div>
          </div>
        </div>

        <!-- TAB: Lokalizacje -->
        <div v-show="explorerTab === 'locations'">
          <!-- Detail panel -->
          <div v-if="selectedLocation && locationMetrics" class="detail-panel">
            <button class="machine-back-btn" @click="selectedLocation = ''; locationSearch = ''; locationMetrics = null">&#8592; Wroc</button>
            <div class="metrics-header">
              <h3>&#128205; {{ selectedLocation }}</h3>
              <div class="period-info">&#128197; Okres: {{ getExplorerPeriodLabel() }}</div>
              <div class="metrics-grid">
                <div class="metric-card">
                  <div class="metric-value">{{ locationMetrics.metrics.contracts_count }}</div>
                  <div class="metric-label">Umow</div>
                </div>
                <div class="metric-card">
                  <div class="metric-value">{{ locationMetrics.metrics.unique_contractors }}</div>
                  <div class="metric-label">Klientow</div>
                </div>
                <div class="metric-card">
                  <div class="metric-value">{{ formatMoney(locationMetrics.metrics.total_revenue) }}</div>
                  <div class="metric-label">Przychod</div>
                </div>
                <div class="metric-card" v-if="explorerPeriod !== 'all'">
                  <div class="metric-value">{{ formatMoney(locationMetrics.metrics.avg_revenue_per_contract) }}</div>
                  <div class="metric-label">Srednio/umowe</div>
                </div>
              </div>
            </div>
            <div class="table-panel" v-if="locationMetrics.top_machines?.length">
              <div class="table-title">&#128664; Top maszyny</div>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Maszyna</th>
                    <th style="text-align:right;">Razy</th>
                    <th style="text-align:right;">Przychod</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="m in locationMetrics.top_machines" :key="m.name">
                    <td>{{ m.name }}</td>
                    <td style="text-align:right;">{{ m.rental_count }}x</td>
                    <td style="text-align:right;font-weight:600;">{{ formatMoney(m.total_revenue) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="table-panel" v-if="locationMetrics.top_contractors?.length">
              <div class="table-title">&#127942; Top kontrahenci</div>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Kontrahent</th>
                    <th style="text-align:right;">Umow</th>
                    <th style="text-align:right;">Przychod</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in locationMetrics.top_contractors" :key="c.contractor_name">
                    <td>{{ c.contractor_name }}</td>
                    <td style="text-align:right;">{{ c.contract_count }}</td>
                    <td style="text-align:right;font-weight:600;">{{ formatMoney(c.total_revenue) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <!-- Search view -->
          <div v-else>
            <div class="explorer-machine-selector" style="margin-bottom: 16px;">
              <label>Szukaj miasto:</label>
              <input v-model="locationSearch" type="text" placeholder="Wpisz nazwe miasta..." class="explorer-search" style="width:320px;" @input="onLocationSearchInput" />
              <div v-if="locationSearchResults.length" class="machine-search-results">
                <div v-for="loc in locationSearchResults" :key="loc.city" class="machine-result-row" @click="pickLocation(loc.city)">
                  <span class="machine-result-name">{{ loc.city }}</span>
                  <span class="machine-result-nr">{{ loc.rentals_count }} umow</span>
                </div>
              </div>
            </div>
            <div v-if="!locationSearch && locationsData.length" class="location-suggestions">
              <div class="table-panel full-width">
                <div class="table-title">Ranking miast ({{ locationsData.length }})</div>
                <table class="stats-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Miasto</th>
                      <th style="text-align:right;">Umow</th>
                      <th style="text-align:right;">Przychod</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="loc in locationsData.slice(0, 20)" :key="loc.city" @click="pickLocation(loc.city)" class="row-clickable">
                      <td style="color:#718096;">{{ loc.rank }}</td>
                      <td style="font-weight:600;">{{ loc.city }}</td>
                      <td style="text-align:right;">{{ loc.rentals_count }}</td>
                      <td style="text-align:right;font-weight:600;">{{ formatMoney(loc.total_revenue) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useStatsStore } from '@/stores/stats'
import api from '@/composables/useApi'
import { useFileDownload } from '@/composables/useFileDownload'
import { useToastStore } from '@/stores/toast'
import { useTargetFolder } from '@/composables/useTargetFolder.js'

Chart.register(...registerables)

const statsStore = useStatsStore()
const { saveToFolder } = useFileDownload()
const toastStore = useToastStore()
const { getStoredFolderName } = useTargetFolder()

const barCanvas = ref(null)
const donutCanvas = ref(null)
let barChart = null
let donutChart = null

const presets = [
  { key: 'month', label: 'Ten miesiąc' },
  { key: 'quarter', label: 'Ten kwartał' },
  { key: 'year', label: 'Ten rok' },
  { key: 'all', label: 'Wszystko' },
]

const activeTab = ref('live')
const activePreset = ref('year')
const customFrom = ref('')
const customTo = ref('')

// ── Historia sub-tabs (RAO-P1-017) ─────────────────────────────────────────
const historySubTab = ref('general')
const categoryLevel = ref('main')
const categoryBarCanvas = ref(null)
let categoryBarChart = null
const errorByCategory = ref(null)

// ── RAO-P1-026: Shared filters ──────────────────────────────────────────────
const sharedArticleType = ref('all')       // 'all' | 'machine' | 'service'
const sharedCategoryMains = ref([])         // array of category names
const catDropdownOpen = ref(false)
const catDropdownRef = ref(null)

// RAO-P1-026: Drilldown state
const drilldownPath = ref([])   // e.g. [] | ['Wozidła'] | ['Wozidła', 'Wózki widłowe']

// RAO-P1-026: Historia sub-tab
const granularity = ref('month')            // 'month' | 'year'
const errorByPeriod = ref(null)
const periodBarCanvas = ref(null)           // dla wykresu Historia
let periodBarChart = null

// ── RAO-P1-026: Column sorting ──────────────────────────────────────────────
const sortKey = ref('revenue')
const sortDir = ref('desc')

// ── RAO-P2-010: Filtr typ pozycji ───────────────────────────────────────────────
const positionType = ref('all')  // 'machines' | 'services' | 'all'

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'history') {
    nextTick(() => renderBarChart())
  } else {
    nextTick(() => renderDonutChart())
  }
}

const liveUtilPct = computed(() => {
  if (!statsStore.currentlyRented?.total_machines) return 0
  return Math.round(statsStore.currentlyRented.total_rented / statsStore.currentlyRented.total_machines * 100)
})

const liveUtilClass = computed(() => {
  const v = liveUtilPct.value
  if (v >= 70) return 'kpi-success'
  if (v >= 40) return 'kpi-warning'
  return 'kpi-danger'
})

function getDateRange(preset) {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  if (preset === 'month') return [new Date(y, m, 1), now]
  if (preset === 'quarter') {
    const qStart = Math.floor(m / 3) * 3
    return [new Date(y, qStart, 1), now]
  }
  if (preset === 'year') return [new Date(y, 0, 1), now]
  if (preset === 'all') return [new Date(2000, 0, 1), new Date(2099, 11, 31)]
  return [null, null]
}

function fmt(d) {
  if (!d) return null
  return d.toISOString().slice(0, 10)
}

async function loadLive() {
  await statsStore.fetchCurrentlyRented()
  await nextTick()
  renderDonutChart()
}

async function loadPeriod() {
  let df, dt
  if (activePreset.value === 'custom') {
    df = customFrom.value || null
    dt = customTo.value || null
  } else {
    const [from, to] = getDateRange(activePreset.value)
    df = fmt(from)
    dt = fmt(to)
  }
  await statsStore.fetchPeriod(df, dt)
  await nextTick()
  renderBarChart()
}

// RAO-P2-010: Ładowanie pozycji z filtrem typu
async function loadPositions() {
  let df, dt
  if (activePreset.value === 'custom') {
    df = customFrom.value || null
    dt = customTo.value || null
  } else {
    const [from, to] = getDateRange(activePreset.value)
    df = fmt(from)
    dt = fmt(to)
  }
  await statsStore.fetchPositions(positionType.value, df, dt)
}

function selectPreset(key) {
  activePreset.value = key
  if (key !== 'custom') {
    loadPeriod()
    if (historySubTab.value === 'categories') {
      loadCategoryData()
    }
    if (historySubTab.value === 'timeline') {
      loadPeriodData()
    }
    if (historySubTab.value === 'general') {
      loadPositions()  // RAO-P2-010: przeładuj pozycje przy zmianie dat
    }
  }
}

// Wywołanie z przycisku "Filtruj" (custom date range) — obsługuje oba sub-taby
function applyPeriodFilter() {
  loadPeriod()
  if (historySubTab.value === 'categories') {
    loadCategoryData()
  }
  if (historySubTab.value === 'timeline') {
    loadPeriodData()
  }
}

// ── RAO-P1-026: Shared filter helpers ───────────────────────────────────────
function setSharedArticleType(type) {
  sharedArticleType.value = type
  reloadActiveSubTab()
}

function reloadActiveSubTab() {
  if (historySubTab.value === 'categories') {
    loadCategoryData()
  } else if (historySubTab.value === 'timeline') {
    loadPeriodData()
  }
}

function handleClickOutsideDropdown(e) {
  if (catDropdownRef.value && !catDropdownRef.value.contains(e.target)) {
    catDropdownOpen.value = false
  }
}

// ── Historia sub-tabs logic (RAO-P1-017/026) ────────────────────────────────
function switchHistorySubTab(tab) {
  historySubTab.value = tab
  if (tab === 'categories') {
    drilldownPath.value = []
    loadCategoryData()
  } else if (tab === 'timeline') {
    loadPeriodData()
  } else {
    nextTick(() => renderBarChart())
  }
}

function setCategoryLevel(level) {
  categoryLevel.value = level
  drilldownPath.value = []  // reset drilldown przy ręcznej zmianie poziomu
  if (historySubTab.value === 'categories') {
    loadCategoryData()
  }
}

// ── RAO-P1-026: Drilldown helpers ───────────────────────────────────────────
function drillDown(categoryName) {
  if (drilldownPath.value.length >= 3) return  // max sub3
  drilldownPath.value = [...drilldownPath.value, categoryName]
  categoryLevel.value = ['main', 'sub1', 'sub2', 'sub3'][drilldownPath.value.length]
  loadCategoryData()
}

function drillTo(depth) {
  drilldownPath.value = drilldownPath.value.slice(0, depth)
  categoryLevel.value = ['main', 'sub1', 'sub2', 'sub3'][drilldownPath.value.length]
  loadCategoryData()
}

function drillBack() {
  if (drilldownPath.value.length === 0) return
  drilldownPath.value = drilldownPath.value.slice(0, -1)
  categoryLevel.value = ['main', 'sub1', 'sub2', 'sub3'][drilldownPath.value.length]
  loadCategoryData()
}

function categoryHasChildren(categoryName) {
  const tree = statsStore.categoriesList || []
  function findNode(nodes, name) {
    for (const node of nodes) {
      if (node.name === name) return node
      const found = findNode(node.children || [], name)
      if (found) return found
    }
    return null
  }
  const node = findNode(tree, categoryName)
  return node ? (node.children?.length > 0) : false
}

// ── RAO-P1-026: Column sort ─────────────────────────────────────────────────
function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

const sortedCategoryItems = computed(() => {
  const items = statsStore.byCategoryData?.items ?? []
  return [...items].sort((a, b) => {
    const va = a[sortKey.value] ?? 0
    const vb = b[sortKey.value] ?? 0
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : Number(vb) - Number(va)
    return sortDir.value === 'asc' ? -cmp : cmp
  })
})

function sortIcon(key) {
  if (sortKey.value !== key) return ''
  return sortDir.value === 'asc' ? ' ▲' : ' ▼'
}

async function loadCategoryData() {
  errorByCategory.value = null
  let df, dt
  if (activePreset.value === 'custom') {
    df = customFrom.value || null
    dt = customTo.value || null
  } else {
    const [from, to] = getDateRange(activePreset.value)
    df = fmt(from)
    dt = fmt(to)
  }

  // Oblicz level z drilldownPath
  const levels = ['main', 'sub1', 'sub2', 'sub3']
  const level = levels[Math.min(drilldownPath.value.length, 3)]

  // Filtry kategorialne z drilldownPath lub shared filter
  const catMain = drilldownPath.value[0]
    ? [drilldownPath.value[0]]
    : (sharedCategoryMains.value.length ? sharedCategoryMains.value : [])
  const catSub1 = drilldownPath.value[1] || null
  const catSub2 = drilldownPath.value[2] || null

  try {
    await statsStore.fetchByCategory(
      level, df, dt,
      catMain, catSub1, catSub2,
      sharedArticleType.value
    )
    await nextTick()
    renderCategoryBarChart()
  } catch (e) {
    errorByCategory.value = e?.response?.data?.detail ?? 'Błąd ładowania danych kategorii'
  }
}

// ── RAO-P1-026: Historia / by-period ────────────────────────────────────────
async function loadPeriodData() {
  errorByPeriod.value = null
  let df, dt
  if (activePreset.value === 'custom') {
    df = customFrom.value || null
    dt = customTo.value || null
  } else {
    const [from, to] = getDateRange(activePreset.value)
    df = fmt(from)
    dt = fmt(to)
  }
  try {
    const catMains = sharedCategoryMains.value.length ? sharedCategoryMains.value : []
    await statsStore.fetchByPeriod(
      granularity.value, df, dt,
      catMains, sharedArticleType.value
    )
    await nextTick()
    renderPeriodBarChart()
  } catch (e) {
    errorByPeriod.value = e?.response?.data?.detail ?? 'Błąd ładowania danych historii'
  }
}

function setGranularity(g) {
  granularity.value = g
  loadPeriodData()
}

// Computed: pivot table data
const pivotData = computed(() => {
  const items = statsStore.byPeriodData?.items
  if (!items?.length) return null

  const periodsSet = new Set(items.map(i => i.period))
  const periods = [...periodsSet].sort()
  const categoriesSet = new Set(items.map(i => i.category_name))

  const map = {}
  items.forEach(i => {
    if (!map[i.category_name]) map[i.category_name] = {}
    map[i.category_name][i.period] = (map[i.category_name][i.period] || 0) + Number(i.revenue)
  })

  const rows = [...categoriesSet].map(cat => ({
    category: cat,
    values: map[cat] || {},
    total: Object.values(map[cat] || {}).reduce((s, v) => s + Number(v), 0),
  })).sort((a, b) => b.total - a.total)

  const totals = {}
  periods.forEach(p => {
    totals[p] = rows.reduce((s, r) => s + Number(r.values[p] || 0), 0)
  })
  const grandTotal = rows.reduce((s, r) => s + r.total, 0)

  return { periods, rows, totals, grandTotal }
})

function formatPeriod(period) {
  if (/^\d{4}-\d{2}$/.test(period)) {
    const [y, m] = period.split('-')
    const months = ['sty','lut','mar','kwi','maj','cze','lip','sie','wrz','paź','lis','gru']
    return `${months[parseInt(m) - 1]} ${y.slice(2)}`
  }
  return period
}

function selectPivotCategory(catName) {
  if (catName === '__all__') return
  sharedCategoryMains.value = [catName]
  reloadActiveSubTab()
}

function renderPeriodBarChart() {
  if (periodBarChart) { periodBarChart.destroy(); periodBarChart = null }
  const items = statsStore.byPeriodData?.items
  if (!periodBarCanvas.value || !items?.length) return

  const periodsSet = new Set(items.map(i => i.period))
  const periods = [...periodsSet].sort()
  const categoriesSet = new Set(items.map(i => i.category_name))
  const categories = [...categoriesSet].slice(0, 8)  // max 8 serii

  const COLORS = [
    'rgba(29, 43, 83, 0.8)',
    'rgba(255, 99, 71, 0.8)',
    'rgba(50, 205, 50, 0.8)',
    'rgba(255, 165, 0, 0.8)',
    'rgba(138, 43, 226, 0.8)',
    'rgba(0, 206, 209, 0.8)',
    'rgba(255, 20, 147, 0.8)',
    'rgba(154, 205, 50, 0.8)',
  ]

  const datasets = categories.map((cat, idx) => ({
    label: cat === '__all__' ? 'Przychód' : cat,
    data: periods.map(p => {
      const item = items.find(i => i.period === p && i.category_name === cat)
      return item ? Number(item.revenue) : 0
    }),
    backgroundColor: COLORS[idx % COLORS.length],
    borderRadius: 3,
  }))

  periodBarChart = new Chart(periodBarCanvas.value.getContext('2d'), {
    type: 'bar',
    data: { labels: periods.map(formatPeriod), datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: categories.length > 1 },
        tooltip: {
          callbacks: {
            label: ctx => {
              const label = ctx.dataset.label
              const periodLabel = ctx.label
              const origPeriod = periods[ctx.dataIndex]
              const item = items.find(i => i.period === origPeriod && (i.category_name === label || label === 'Przychód'))
              if (item) return `${label}: ${formatMoney(item.revenue)} · ${item.contracts_count} umów · ${item.rented_days} dni`
              return `${label}: ${formatMoney(ctx.parsed.y)}`
            }
          }
        }
      },
      scales: {
        y: {
          ticks: { callback: v => v >= 1000 ? Math.round(v / 1000) + 'k' : v },
        }
      }
    }
  })
}

function renderCategoryBarChart() {
  if (categoryBarChart) categoryBarChart.destroy()
  if (!categoryBarCanvas.value || !statsStore.byCategoryData?.items?.length) return

  const items = statsStore.byCategoryData.items.slice(0, 15)
  const labels = items.map(i => {
    const n = i.category_name
    return n.length > 28 ? n.slice(0, 28) + '...' : n
  })
  const data = items.map(i => Number(i.revenue))

  categoryBarChart = new Chart(categoryBarCanvas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Przychód (zł)',
        data,
        backgroundColor: 'rgba(15, 35, 78, 0.75)',
        hoverBackgroundColor: 'rgba(15, 35, 78, 0.95)',
        borderRadius: 4,
        barThickness: 22,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const item = items[ctx.dataIndex]
              return `${formatMoney(item.revenue)} · ${item.rented_days} dni · ${item.contracts_count} umów`
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            callback: (v) => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v,
            font: { size: 11 },
          },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        y: {
          ticks: { font: { size: 11 } },
          grid: { display: false },
        },
      },
    },
  })
}

const maxCategoryRevenue = computed(() => {
  if (!statsStore.byCategoryData?.items?.length) return 1
  return Math.max(...statsStore.byCategoryData.items.map(i => Number(i.revenue)))
})

const totalCategoryDays = computed(() => {
  if (!statsStore.byCategoryData?.items?.length) return 0
  return statsStore.byCategoryData.items.reduce((sum, i) => sum + i.rented_days, 0)
})

function categoryBarWidth(val) {
  return Math.round(Number(val) / maxCategoryRevenue.value * 100)
}

async function printPage() {
  try {
    let df = null, dt = null
    if (activePreset.value === 'custom') {
      df = customFrom.value || null
      dt = customTo.value || null
    } else {
      const [from, to] = getDateRange(activePreset.value)
      df = fmt(from)
      dt = fmt(to)
    }
    const response = await api.get('/reports/summary/stats', {
      params: { date_from: df, date_to: dt },
      responseType: 'blob',
    })
    const cd = response.headers['content-disposition'] || ''
    // Parsowanie nazwy pliku z Content-Disposition
    let filename = 'Statystyki.pdf'
    const rfc5987 = cd.match(/filename\*=UTF-8''([^;]+)/i)
    if (rfc5987) {
      try { filename = decodeURIComponent(rfc5987[1]) } catch { }
    } else {
      const classic = cd.match(/filename="?([^";\n]+)"?/i)
      if (classic) filename = classic[1].trim()
    }
    const saved = await saveToFolder(response.data, cd, filename, 'zestawienia')
    if (saved) {
      const folderName = await getStoredFolderName()
      toastStore.showToast(`${filename} zapisany do folderu ${folderName}/Zestawienia`, 'success')
    }
  } catch {
    alert('B\u0142\u0105d generowania PDF')
  }
}

const utilClass = computed(() => {
  if (!statsStore.summary) return ''
  const v = statsStore.summary.utilization_pct
  if (v >= 70) return 'kpi-success'
  if (v >= 40) return 'kpi-warning'
  return 'kpi-danger'
})

const maxFeeRevenue = computed(() => {
  if (!statsStore.additionalFees?.breakdown?.length) return 1
  return Math.max(...statsStore.additionalFees.breakdown.map(s => Number(s.total_revenue)))
})

const maxLocCount = computed(() => {
  if (!statsStore.locations.length) return 1
  return Math.max(...statsStore.locations.map(l => l.rentals_count))
})

function feeBarWidth(val) {
  return Math.round(Number(val) / maxFeeRevenue.value * 100)
}

function locBarWidth(val) {
  return Math.round(val / maxLocCount.value * 100)
}

function formatMoney(v) {
  if (!v && v !== 0) return '—'
  return Number(v).toLocaleString('pl-PL', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' zł'
}

// ═══════════════════════════════════════════════════════
// EKSPLORATOR — Zmienne i funkcje
// ═══════════════════════════════════════════════════════

const explorerTab = ref('all')
const explorerQuery = ref('')
const explorerPeriod = ref('year')
const explorerCustomFrom = ref('')
const explorerCustomTo = ref('')
const loadingExplorer = ref(false)
const explorerResults = ref([])
const explorerSummary = ref({ count: 0, revenue: 0 })
const selectedMachine = ref('')
const availableMachines = ref([])
const machineDetails = ref(null)
const machineSearch = ref('')
const machineSearchResults = ref([])
let machineSearchTimer = null
const selectedService = ref('')
const servicesData = ref([])
const serviceDetails = ref(null)
const serviceSearch = ref('')
const serviceSearchResults = ref([])
let serviceSearchTimer = null
const selectedLocation = ref('')
const locationSearch = ref('')
const locationSearchResults = ref([])
const locationMetrics = ref(null)
const locationsData = ref([])

const explorerPresets = [
  { key: 'month', label: 'Ten miesiąc' },
  { key: 'quarter', label: 'Ten kwartał' },
  { key: 'year', label: 'Ten rok' },
  { key: 'all', label: 'Wszystko' },
]

const SERVICE_GROUPS = [
  { key: 'teleskopowa', label: 'Ładowarki tel.', pattern: /ładowark.*teleskop/i },
  { key: 'obrotowa', label: 'Ładowarki obr.', pattern: /ładowark.*obrotow/i },
  { key: 'widlowy', label: 'Wózki widłowe', pattern: /w[oó][zź]k.*widłow/i },
  { key: 'zuraw', label: 'Żurawie / HDS', pattern: /(żuraw|HDS|manipulat)/i },
  { key: 'podnosnik', label: 'Podnośniki', pattern: /(podnośnik|podest)/i },
  { key: 'minikoparka', label: 'Minikoparki', pattern: /minikopark/i },
  { key: 'operator', label: 'Usługi operatorskie', pattern: /operator/i },
  { key: 'transport', label: 'Transport', pattern: /transport/i },
  { key: 'inne', label: 'Inne', pattern: null },
]

function classifyService(name) {
  for (const g of SERVICE_GROUPS) {
    if (g.pattern && g.pattern.test(name)) return g.key
  }
  return 'inne'
}

const serviceGroups = computed(() => {
  const counts = {}
  for (const s of servicesData.value) {
    const key = classifyService(s.service_name)
    counts[key] = (counts[key] || 0) + 1
  }
  return SERVICE_GROUPS.filter(g => counts[g.key]).map(g => ({ ...g, count: counts[g.key] }))
})

const filteredServices = computed(() => {
  if (!selectedService.value) return servicesData.value
  return servicesData.value.filter(s => classifyService(s.service_name) === selectedService.value)
})

function filterService(key) {
  selectedService.value = key
}

function setExplorerPeriod(key) {
  explorerPeriod.value = key
  if (key !== 'custom') onExplorerPeriodChange()
}

function onExplorerPeriodChange() {
  const tab = explorerTab.value
  if (tab === 'all' && explorerQuery.value.trim()) searchExplorer()
  if (tab === 'services') loadServicesData()
  if (tab === 'locations') loadLocationsData()
  if (tab === 'machines' && selectedMachine.value) loadMachineDetails()
}

function switchExplorerTab(tab) {
  explorerTab.value = tab
  if (tab === 'machines' && availableMachines.value.length === 0) loadAvailableMachines()
  if (tab === 'services') loadServicesData()
  if (tab === 'locations') loadLocationsData()
}

function onMachineSearchInput() {
  if (machineSearchTimer) clearTimeout(machineSearchTimer)
  machineDetails.value = null
  selectedMachine.value = ''
  const q = machineSearch.value.trim().toLowerCase()
  if (!q || q.length < 2) {
    machineSearchResults.value = []
    return
  }
  machineSearchTimer = setTimeout(() => {
    machineSearchResults.value = availableMachines.value.filter(m =>
      (m.name && m.name.toLowerCase().includes(q)) ||
      (m.internal_number && m.internal_number.toLowerCase().includes(q))
    ).slice(0, 15)
  }, 200)
}

function onServiceSearchInput() {
  if (serviceSearchTimer) clearTimeout(serviceSearchTimer)
  serviceDetails.value = null
  const q = serviceSearch.value.trim().toLowerCase()
  if (!q || q.length < 2) {
    serviceSearchResults.value = []
    return
  }
  serviceSearchTimer = setTimeout(() => {
    serviceSearchResults.value = servicesData.value.filter(s =>
      (s.service_name && s.service_name.toLowerCase().includes(q))
    ).slice(0, 15)
  }, 200)
}

function pickService(articleId) {
  const service = servicesData.value.find(s => s.article_id === articleId)
  if (service) {
    serviceSearch.value = service.service_name
    serviceSearchResults.value = []
    openServiceDetails(service)
  }
}

function pickMachine(id) {
  selectedMachine.value = id
  machineSearchResults.value = []
  const m = availableMachines.value.find(x => x.id === id)
  if (m) machineSearch.value = m.name + (m.internal_number ? ` [${m.internal_number}]` : '')
  loadMachineDetails()
}

function pickFirstMachine() {
  if (machineSearchResults.value.length) pickMachine(machineSearchResults.value[0].id)
}

function openExplorerItem(item) {
  if (item.type_label === 'Maszyna' && item.article_id) {
    explorerTab.value = 'machines'
    if (availableMachines.value.length === 0) {
      loadAvailableMachines().then(() => pickMachine(item.article_id))
    } else {
      pickMachine(item.article_id)
    }
  } else if (item.type_label === 'Us\u0142uga') {
    explorerTab.value = 'services'
    loadServicesData()
  }
}

function getExplorerDateRange() {
  if (explorerPeriod.value === 'custom') {
    return [
      explorerCustomFrom.value ? new Date(explorerCustomFrom.value) : null,
      explorerCustomTo.value ? new Date(explorerCustomTo.value) : null,
    ]
  }
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  switch (explorerPeriod.value) {
    case 'month': return [new Date(y, m, 1), now]
    case 'quarter': return [new Date(y, Math.floor(m / 3) * 3, 1), now]
    case 'year': return [new Date(y, 0, 1), now]
    default: return [null, null]
  }
}

async function searchExplorer() {
  if (!explorerQuery.value.trim()) {
    explorerResults.value = []
    explorerSummary.value = { count: 0, revenue: 0 }
    return
  }
  loadingExplorer.value = true
  try {
    const [from, to] = getExplorerDateRange()
    const params = {
      q: explorerQuery.value,
      date_from: from?.toISOString().slice(0, 10),
      date_to: to?.toISOString().slice(0, 10),
      limit: 50,
    }
    const { data } = await api.get('/explorer/search', { params })
    explorerResults.value = data.items || []
    explorerSummary.value = data.summary || { count: 0, revenue: 0 }
  } catch (e) {
    console.error('Explorer search error:', e)
  } finally {
    loadingExplorer.value = false
  }
}

async function loadAvailableMachines() {
  try {
    const { data } = await api.get('/articles', { params: { limit: 1000 } })
    availableMachines.value = (data.items || data).filter(a => !a.is_service)
  } catch (e) {
    console.error('Error loading machines:', e)
  }
}

async function loadMachineDetails() {
  if (!selectedMachine.value) {
    machineDetails.value = null
    return
  }
  loadingExplorer.value = true
  try {
    const [from, to] = getExplorerDateRange()
    const params = {
      date_from: from?.toISOString().slice(0, 10),
      date_to: to?.toISOString().slice(0, 10),
    }
    const { data } = await api.get(`/explorer/machines/${selectedMachine.value}`, { params })
    machineDetails.value = data
  } catch (e) {
    console.error('Error loading machine details:', e)
  } finally {
    loadingExplorer.value = false
  }
}

async function loadServicesData() {
  loadingExplorer.value = true
  try {
    const [from, to] = getExplorerDateRange()
    const params = {
      date_from: from?.toISOString().slice(0, 10),
      date_to: to?.toISOString().slice(0, 10),
    }
    const { data } = await api.get('/explorer/services', { params })
    servicesData.value = data.services || []
  } catch (e) {
    console.error('Error loading services:', e)
  } finally {
    loadingExplorer.value = false
  }
}

async function loadLocationsData() {
  loadingExplorer.value = true
  try {
    const [from, to] = getExplorerDateRange()
    const params = {
      date_from: from?.toISOString().slice(0, 10),
      date_to: to?.toISOString().slice(0, 10),
      limit: 50,
    }
    const { data } = await api.get('/explorer/locations', { params })
    locationsData.value = data.locations || []
  } catch (e) {
    console.error('Error loading locations:', e)
  } finally {
    loadingExplorer.value = false
  }
}

function onLocationSearchInput() {
  const q = locationSearch.value.trim().toLowerCase()
  if (!q || q.length < 2) {
    locationSearchResults.value = []
    return
  }
  locationSearchResults.value = locationsData.value.filter(l =>
    l.city.toLowerCase().includes(q)
  ).slice(0, 15)
}

function pickLocation(city) {
  selectedLocation.value = city
  locationSearchResults.value = []
  locationSearch.value = city
  loadLocationDetails(city)
}

async function loadLocationDetails(city) {
  loadingExplorer.value = true
  try {
    const [from, to] = getExplorerDateRange()
    const params = {
      date_from: from?.toISOString().slice(0, 10),
      date_to: to?.toISOString().slice(0, 10),
    }
    const { data } = await api.get(`/explorer/locations/${encodeURIComponent(city)}`, { params })
    if (data.error) {
      console.error('Backend error:', data)
      // Instead of undefined, show zero data
      locationMetrics.value = {
        metrics: {
          contracts_count: 0,
          unique_contractors: 0,
          total_revenue: 0,
          avg_revenue_per_contract: 0
        },
        top_machines: [],
        top_contractors: []
      }
    } else {
      locationMetrics.value = data
    }
  } catch (e) {
    console.error('Error loading location details:', e)
    // Also handle catch case with zero data
    locationMetrics.value = {
      metrics: {
        contracts_count: 0,
        unique_contractors: 0,
        total_revenue: 0,
        avg_revenue_per_contract: 0
      },
      top_machines: [],
      top_contractors: []
    }
  } finally {
    loadingExplorer.value = false
  }
}

function openServiceDetails(service) {
  selectedService.value = ''
  loadServiceDetails(service.article_id)
}

async function loadServiceDetails(articleId) {
  loadingExplorer.value = true
  try {
    const [from, to] = getExplorerDateRange()
    const params = {
      date_from: from?.toISOString().slice(0, 10),
      date_to: to?.toISOString().slice(0, 10),
    }
    const { data } = await api.get(`/explorer/services/${articleId}`, { params })
    if (data.error) {
      console.error('Backend error:', data)
      // Instead of closing panel, show zero data
      // Use existing service name from current details or try to find it
      const existingName = serviceDetails.value?.service?.name
      const service = servicesData.value.find(s => s.article_id === articleId)
      const serviceName = existingName || service?.service_name || `Usługa ${articleId}`
      
      serviceDetails.value = {
        service: {
          id: articleId,
          name: serviceName
        },
        metrics: {
          times_billed: 0,
          total_revenue: 0,
          avg_revenue_per_contract: 0
        },
        top_contractors: [],
        location_breakdown: []
      }
    } else {
      serviceDetails.value = data
    }
  } catch (e) {
    console.error('Error loading service details:', e)
    // Also handle catch case with zero data
    const existingName = serviceDetails.value?.service?.name
    const service = servicesData.value.find(s => s.article_id === articleId)
    const serviceName = existingName || service?.service_name || `Usługa ${articleId}`
    
    serviceDetails.value = {
      service: {
        id: articleId,
        name: serviceName
      },
      metrics: {
        times_billed: 0,
        total_revenue: 0,
        avg_revenue_per_contract: 0
      },
      top_contractors: [],
      location_breakdown: []
    }
  } finally {
    loadingExplorer.value = false
  }
}

function getExplorerPeriodLabel() {
  const p = explorerPeriod.value
  if (p === 'month') return 'Ten miesiac'
  if (p === 'quarter') return 'Ten kwartaL'
  if (p === 'year') return 'Ten rok'
  if (p === 'all') return 'Wszystko'
  if (p === 'custom') return 'Wlasny okres'
  return p
}

function renderCharts() {
  renderBarChart()
  renderDonutChart()
}

function renderBarChart() {
  if (barChart) barChart.destroy()
  if (!barCanvas.value || !statsStore.topMachines.length) return

  const labels = statsStore.topMachines.map(m => {
    const num = m.internal_number ? `[${m.internal_number}] ` : ''
    const name = m.name.length > 25 ? m.name.slice(0, 25) + '...' : m.name
    return num + name
  })
  const data = statsStore.topMachines.map(m => Number(m.revenue))

  barChart = new Chart(barCanvas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Przychód (zł)',
        data,
        backgroundColor: 'rgba(15, 35, 78, 0.75)',
        hoverBackgroundColor: 'rgba(15, 35, 78, 0.95)',
        borderRadius: 4,
        barThickness: 22,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const m = statsStore.topMachines[ctx.dataIndex]
              return `${formatMoney(m.revenue)} · ${m.rented_days} dni · ${m.contracts_count} umów`
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            callback: (v) => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v,
            font: { size: 11 },
          },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        y: {
          ticks: { font: { size: 11 } },
          grid: { display: false },
        },
      },
    },
  })
}

function renderDonutChart() {
  if (donutChart) donutChart.destroy()
  if (!donutCanvas.value || !statsStore.currentlyRented) return

  const rented = statsStore.currentlyRented.total_rented
  const free = statsStore.currentlyRented.total_machines - rented

  donutChart = new Chart(donutCanvas.value.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Wynajęte', 'Dostępne'],
      datasets: [{
        data: [rented, Math.max(free, 0)],
        backgroundColor: ['#0F234E', '#E2E8F0'],
        hoverBackgroundColor: ['#1A3266', '#CBD5E0'],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 12 }, padding: 16 },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.raw} maszyn`,
          },
        },
      },
    },
    plugins: [{
      id: 'centerText',
      afterDraw(chart) {
        const { ctx, chartArea } = chart
        const cx = (chartArea.left + chartArea.right) / 2
        const cy = (chartArea.top + chartArea.bottom) / 2
        ctx.save()
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.font = 'bold 28px Inter, sans-serif'
        ctx.fillStyle = '#0F234E'
        ctx.fillText(rented, cx, cy - 8)
        ctx.font = '11px Inter, sans-serif'
        ctx.fillStyle = '#718096'
        ctx.fillText('wynajętych', cx, cy + 14)
        ctx.restore()
      },
    }],
  })
}

// Watch for period changes to reload data
watch(explorerPeriod, () => {
  onExplorerPeriodChange()
  // Reload details if they are open
  if (serviceDetails.value) {
    loadServiceDetails(serviceDetails.value.service?.id)
  }
  if (locationMetrics.value && selectedLocation.value) {
    loadLocationDetails(selectedLocation.value)
  }
})

watch(explorerCustomFrom, () => {
  if (explorerPeriod.value === 'custom') {
    onExplorerPeriodChange()
    // Reload details if they are open
    if (serviceDetails.value) {
      loadServiceDetails(serviceDetails.value.service?.id)
    }
    if (locationMetrics.value && selectedLocation.value) {
      loadLocationDetails(selectedLocation.value)
    }
  }
})

watch(explorerCustomTo, () => {
  if (explorerPeriod.value === 'custom') {
    onExplorerPeriodChange()
    // Reload details if they are open
    if (serviceDetails.value) {
      loadServiceDetails(serviceDetails.value.service?.id)
    }
    if (locationMetrics.value && selectedLocation.value) {
      loadLocationDetails(selectedLocation.value)
    }
  }
})

// RAO-P2-010: Watch na positionType - przeładuj pozycje przy zmianie filtra
watch(positionType, () => {
  if (historySubTab.value === 'general') {
    loadPositions()
  }
})

// RAO-P1-026: Watch na sharedCategoryMains — przeładuj przy zmianie selekcji
watch(sharedCategoryMains, () => {
  reloadActiveSubTab()
}, { deep: true })

onMounted(async () => {
  loadLive()
  loadPeriod()
  loadPositions()  // RAO-P2-010: załaduj pozycje przy starcie
  document.addEventListener('click', handleClickOutsideDropdown)
  await statsStore.fetchCategoriesList()  // RAO-P1-026: załaduj drzewo kategorii
})

onBeforeUnmount(() => {
  if (barChart) barChart.destroy()
  if (donutChart) donutChart.destroy()
  if (categoryBarChart) categoryBarChart.destroy()
  if (periodBarChart) { periodBarChart.destroy(); periodBarChart = null }
  document.removeEventListener('click', handleClickOutsideDropdown)
  // RAO-P1-043: cleanup timerów wyszukiwania — zapobiega memory leakom
  if (machineSearchTimer) clearTimeout(machineSearchTimer)
  if (serviceSearchTimer) clearTimeout(serviceSearchTimer)
})
</script>

<style scoped>
.reports-dashboard { padding: 0; }

.tabs-bar {
  display: flex;
  gap: 4px;
}

.current-status-header {
  background: linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%);
  border-left: 4px solid var(--color-primary);
  padding: 16px 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.current-status-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.current-status-subtitle {
  font-size: 13px;
  color: #718096;
  font-style: italic;
}

.tabs-bar {
  display: flex;
  gap: 4px;
}

.tab {
  padding: 10px 20px;
  border: none;
  background: transparent;
  color: #718096;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 150ms, border-color 150ms;
  font-family: inherit;
  border-radius: 6px 6px 0 0;
}
.tab:hover { color: #0F234E; background: #F7FAFC; }
.tab-active {
  color: #0F234E;
  font-weight: 700;
  border-bottom-color: #0F234E;
  background: transparent;
}
.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CBD5E0;
  transition: background 150ms;
}
.tab-dot-active {
  background: #38A169;
  box-shadow: 0 0 0 3px rgba(56,161,105,0.2);
}

.kpi-row-live {
  grid-template-columns: repeat(3, 1fr);
}
.kpi-live-accent {
  background: linear-gradient(135deg, #0F234E 0%, #1A3266 100%);
}

.empty-state {
  color: #A0AEC0;
  font-size: 13px;
  padding: 24px 0;
}

.explorer-placeholder {
  text-align: center;
  padding: 80px 20px;
  background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%);
  border-radius: 16px;
  margin-top: 20px;
}
.explorer-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.explorer-title {
  font-size: 18px;
  font-weight: 700;
  color: #0F234E;
  margin-bottom: 8px;
}
.explorer-desc {
  font-size: 14px;
  color: #718096;
  margin-bottom: 20px;
  line-height: 1.5;
}
.explorer-coming {
  display: inline-block;
  padding: 8px 16px;
  background: #0F234E;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  border-radius: 99px;
}

.date-pills {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.pill {
  padding: 7px 16px;
  border-radius: 99px;
  border: 1px solid #E2E8F0;
  background: #fff;
  color: #4A5568;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms;
  font-family: inherit;
}
.pill:hover { border-color: #0F234E; color: #0F234E; }
.pill.active { background: #0F234E; color: #fff; border-color: #0F234E; }
.pill-custom { display: flex; align-items: center; gap: 6px; }
.pill-date {
  padding: 5px 10px;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 12px;
  font-family: inherit;
}
.pill-go { padding: 6px 14px; font-size: 12px; }

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.kpi-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 18px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  text-align: center;
  transition: box-shadow 250ms;
}
.kpi-card:hover { box-shadow: 0 6px 20px rgba(15,35,78,0.1); }
.kpi-value {
  font-size: 32px;
  font-weight: 800;
  color: #0F234E;
  line-height: 1.1;
}
.kpi-value.kpi-small { font-size: 16px; font-weight: 700; }
.kpi-value.kpi-muted { color: #CBD5E0; }
.kpi-accent { color: #0F234E; }
.kpi-success { color: #38A169; }
.kpi-warning { color: #D69E2E; }
.kpi-danger { color: #E53E3E; }
.kpi-label {
  font-size: 12px;
  font-weight: 600;
  color: #718096;
  margin-top: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.kpi-sub {
  font-size: 11px;
  color: #A0AEC0;
  margin-top: 2px;
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.chart-panel {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  position: relative;
}
.chart-wrap {
  position: relative;
  width: 100%;
}
.chart-title {
  font-size: 14px;
  font-weight: 700;
  color: #0F234E;
  margin-bottom: 12px;
}
.chart-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #A0AEC0;
  font-size: 13px;
}

.tables-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.table-panel {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.table-panel.full-width { grid-column: 1 / -1; }
.table-title {
  font-size: 14px;
  font-weight: 700;
  color: #0F234E;
  margin-bottom: 10px;
}
.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.stats-table th {
  text-align: left;
  padding: 6px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border-bottom: 2px solid #E2E8F0;
}
.stats-table td {
  padding: 7px 8px;
  border-bottom: 1px solid #F0F0F0;
  color: #4A5568;
}
.stats-table tfoot td {
  border-top: 2px solid #E2E8F0;
  border-bottom: none;
  padding-top: 10px;
}
.stats-table tbody tr:hover { background: #F7FAFC; }
.stats-table tbody tr.row-clickable { cursor: pointer; }
.stats-table tbody tr.row-clickable:hover { background: #EBF4FF; }

.bar-bg {
  height: 6px;
  background: #EDF2F7;
  border-radius: 3px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: #0F234E;
  border-radius: 3px;
  transition: width 600ms ease;
}
.bar-fill-blue {
  background: #3182CE;
}

.rented-scroll {
  max-height: 300px;
  overflow: auto;
}

.reports-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: #718096;
  font-size: 14px;
}
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #E2E8F0;
  border-top-color: #0F234E;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.kpi-highlight {
  background: linear-gradient(135deg, #0F234E 0%, #1A3266 100%);
}
.kpi-highlight .kpi-value { color: #fff; }
.kpi-highlight .kpi-label { color: rgba(255,255,255,0.7); }
.kpi-highlight .kpi-sub { color: rgba(255,255,255,0.5); }

@media (max-width: 1100px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
  .tables-row { grid-template-columns: 1fr; }
}

/* Eksplorator styles */
.explorer-period-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.period-label {
  font-size: 13px;
  font-weight: 600;
  color: #4A5568;
  margin-right: 4px;
}

.machine-search-results {
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 16px;
}
.machine-result-row {
  padding: 10px 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #F0F0F0;
  transition: background 100ms;
}
.machine-result-row:last-child { border-bottom: none; }
.machine-result-row:hover { background: #EBF4FF; }
.machine-result-name { font-size: 14px; color: #2D3748; font-weight: 500; }
.machine-result-nr { font-size: 12px; color: #718096; }
.search-hint { font-size: 13px; color: #718096; }
.machine-back-btn {
  border: none;
  background: transparent;
  color: #3182CE;
  font-size: 13px;
  cursor: pointer;
  padding: 6px 0;
  margin-bottom: 8px;
  font-family: inherit;
}
.machine-back-btn:hover { text-decoration: underline; }

.chip-count {
  display: inline-block;
  background: rgba(15,35,78,0.1);
  color: #0F234E;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 99px;
  margin-left: 4px;
  font-weight: 600;
}
.service-chip.active .chip-count {
  background: rgba(255,255,255,0.25);
  color: #fff;
}

.explorer-subtabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid #E2E8F0;
  padding-bottom: 0;
}
.subtab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #718096;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 150ms;
}
.subtab:hover { color: #0F234E; }
.subtab-active {
  color: #0F234E;
  font-weight: 600;
  border-bottom-color: #0F234E;
}

.explorer-filters {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filter-group label {
  font-size: 13px;
  font-weight: 600;
  color: #4A5568;
}
.explorer-search {
  padding: 8px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  width: 280px;
}
.explorer-search:focus {
  outline: none;
  border-color: #0F234E;
}
.explorer-select {
  padding: 8px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}
.explorer-select:focus {
  outline: none;
  border-color: #0F234E;
}

.explorer-summary {
  background: #F7FAFC;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #4A5568;
  margin-top: 12px;
}

.explorer-machine-selector {
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.explorer-machine-selector label {
  font-size: 14px;
  font-weight: 600;
  color: #4A5568;
}

.machine-metrics {
  margin-bottom: 16px;
}
.metrics-header {
  background: linear-gradient(135deg, #0F234E 0%, #1A3266 100%);
  color: #fff;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 16px;
}
.metrics-header h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #fff;
}
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.metric-card {
  text-align: center;
  padding: 12px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
}
.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}
.metric-label {
  font-size: 11px;
  color: rgba(255,255,255,0.7);
  margin-top: 4px;
}

.service-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.service-chip {
  padding: 6px 14px;
  border-radius: 99px;
  border: 1px solid #E2E8F0;
  background: #fff;
  color: #4A5568;
  font-size: 13px;
  cursor: pointer;
  transition: all 150ms;
}
.service-chip:hover { border-color: #0F234E; }
.service-chip.active {
  background: #0F234E;
  color: #fff;
  border-color: #0F234E;
}

.period-info {
  font-size: 13px;
  color: #718096;
  margin-bottom: 12px;
}

.detail-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.location-suggestions {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .explorer-filters { flex-direction: column; }
  .explorer-search { width: 100%; }
}

/* ── RAO-P1-017: Category stats styles ──────────────────────────────────── */
.category-level-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.category-error-state {
  background: #FFF5F5;
  color: #C53030;
  padding: 14px 16px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
  border: 1px solid #FEB2B2;
}

/* ── RAO-P2-010: Position type filter styles ───────────────────────────────── */
.position-type-filter {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  padding: 8px 0;
}
.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: #718096;
}
.positions-summary {
  margin-top: 12px;
  padding: 8px 12px;
  background: #F7FAFC;
  border-radius: 6px;
  font-size: 13px;
  color: #4A5568;
}

/* ── RAO-P1-026: Shared filter bar ─────────────────────────────────────────── */
.shared-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--color-bg-light, #F8F9FA);
  border-radius: var(--border-radius, 8px);
  align-items: center;
}

.shared-cat-dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 8px;
  min-width: 200px;
  max-height: 250px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
  color: #4A5568;
}
.dropdown-item:hover { background: #F7FAFC; }

.dropdown-clear {
  display: block;
  width: 100%;
  margin-top: 6px;
  padding: 4px;
  font-size: 12px;
  color: #E53E3E;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.dropdown-clear:hover { text-decoration: underline; }

.dropdown-trigger {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── RAO-P1-026: Drilldown & breadcrumb ────────────────────────────────────── */
.drilldown-breadcrumb {
  font-size: 13px;
  margin-bottom: 12px;
  color: #718096;
}
.breadcrumb-item.clickable {
  color: #0F234E;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: text-decoration-color 150ms;
}
.breadcrumb-item.clickable:hover { text-decoration-color: currentColor; }
.breadcrumb-sep { margin: 0 4px; }
.drilldown-row:hover { background: #EBF4FF !important; }
.drilldown-arrow {
  display: inline-block;
  margin-left: 4px;
  color: #718096;
  font-size: 16px;
  line-height: 1;
}

/* ── RAO-P1-026: Pivot table ────────────────────────────────────────────────── */
.pivot-table th, .pivot-table td {
  white-space: nowrap;
}

/* ── RAO-P1-026: btn-link helper ────────────────────────────────────────────── */
.btn-link {
  background: none;
  border: none;
  color: #3182CE;
  cursor: pointer;
  font-size: 13px;
  padding: 0 4px;
  font-family: inherit;
  text-decoration: underline;
}
.btn-link:hover { color: #2c5282; }

/* Przycisk cofnij nad tabelą kategorii */
.drillback-main-btn {
  background: var(--color-primary, #1D2B53);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--border-radius-md, 12px);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.2s ease;
}

.drillback-main-btn:hover {
  background: #2a3a6a;
  transform: translateY(-1px);
}

.drillback-main-btn:active {
  transform: translateY(0);
}

/* RAO-P2-021: Banner informacyjny o danych historycznych (sekcja Kategorie) */
.history-banner {
  background: var(--color-bg-light, #f0f4ff);
  border-left: 3px solid var(--color-primary, #1D2B53);
  border-radius: 0 var(--border-radius-md, 12px) var(--border-radius-md, 12px) 0;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--color-text-muted, #555);
  margin-bottom: 12px;
}
</style>
