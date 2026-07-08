<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack">←</button>
      <span class="toolbar-info">{{ isEdit ? (contractStore.current?.number ? `Umowa: ${contractStore.current.number}` : 'Ładowanie...') : 'Nowa umowa' }}</span>
      <!-- RAO-P2-022: badge rozliczona -->
      <span v-if="isEdit && form.is_settled" class="settled-badge">✓ Rozliczona</span>
      <button v-if="isEdit" class="toolbar-btn" title="Drukuj PDF" @click="generateReport('contract')">⎙</button>
      <button v-if="isEdit" class="toolbar-btn" title="Protokół ZO" @click="generateReport('protocol_zo')">📄</button>
      <button v-if="isEdit" class="toolbar-btn" title="Przelicz wartość" @click="recalcTotal">∑</button>
      <button v-if="isEdit" class="toolbar-btn" title="Pobierz koszty z Fakturownia" @click="handleFakturownia">💰</button>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area" style="padding:var(--spacing-md);overflow-y:auto;">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else style="max-width:1100px;margin:0 auto;">
        <!-- Section 1: Dane podstawowe -->
        <div class="page-card" style="margin-bottom:var(--spacing-md);">
          <h3 class="section-title">Dane podstawowe</h3>
          <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
          <div class="form-row-4" style="align-items:start;">
            <div class="form-group">
              <label class="form-label">Typ umowy</label>
              <select v-model="form.contract_type" class="form-control" :disabled="isEdit">
                <option value="S">Umowa najmu (S)</option>
                <option value="U">Umowa usługi (U)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Numer umowy</label>
              <input :value="contractStore.current?.number || '(auto)'" type="text" class="form-control" disabled />
            </div>
            <div class="form-group">
              <label class="form-label">OID Fakturownia (opcjonalny)</label>
              <input v-model="form.oid" type="text" class="form-control" placeholder="(auto = numer umowy)" pattern="[A-Za-z0-9\-/_]+" maxlength="40" />
              <small style="color:var(--color-text-muted);">Puste = użyj numeru umowy. Tylko litery, cyfry, -, /, _.</small>
            </div>
            <div class="form-group">
              <label class="form-label">Okres umowy *</label>
              <ContractPeriodPicker
                v-model:working-days-per-week="form.working_days_per_week"
                :date-from="form.date_from"
                :date-to="form.date_to"
                @update:date-from="form.date_from = $event"
                @update:date-to="form.date_to = $event"
              />
              <span v-if="!form.date_from" class="field-error">Podaj datę od</span>
            </div>
          </div>
        </div>

        <!-- Section 2: Kontrahent i adres -->
        <div class="page-card" style="margin-bottom:var(--spacing-md);">
          <h3 class="section-title">Kontrahent i adres dostawy</h3>
          <div class="form-row-2" style="align-items:start;">
            <div class="form-group">
              <label class="form-label">Kontrahent *</label>
              <div style="display:flex;gap:8px;">
                <input :value="contractorName" type="text" class="form-control" disabled placeholder="Wybierz kontrahenta..." style="flex:1;" :class="{ 'error': !form.contractor_id }" />
                <button type="button" class="btn btn-secondary btn-sm" @click="showContractorPicker = true">Wybierz</button>
              </div>
              <span v-if="!form.contractor_id" class="field-error">Wybierz kontrahenta</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Adres dostawy</label>
            <div class="address-layout">
              <div class="address-row">
                <select v-if="contractorAddresses.length" v-model="selectedAddressId" class="form-control address-select" @change="onAddressSelect">
                  <option :value="null">— wpisz ręcznie —</option>
                  <option v-for="addr in contractorAddresses" :key="addr.id" :value="addr.id">
                    {{ addr.name || addr.city }} — {{ addr.street || '' }} {{ addr.postal_code || '' }}
                  </option>
                </select>
              </div>
              <div class="address-row" style="margin-top:4px;">
                <label class="checkbox-group" style="font-size:12px;">
                  <input type="checkbox" v-model="manualAddressMode" />
                  <span>Ręczny adres (wyłącz auto-fill z PNA/Nominatim)</span>
                </label>
              </div>
              <div class="address-row">
                <input v-model="form.postal_code" @blur="onPostalCodeBlur" @input="onPostalInput" class="form-control postal-input" placeholder="00-000" maxlength="6" data-testid="contract-postal-code" title="Pozostaje edytowalne; auto-fill PNA/Nominatim wyłącza się powyżej" />
                <input v-model="form.city" @input="onCityInput" class="form-control city-input" placeholder="Miasto" :class="{ 'input-loading': pnaLoading && !manualAddressMode }" data-testid="contract-city" title="Pozostaje edytowalne; auto-fill PNA/Nominatim wyłącza się powyżej" />
                <div v-if="pnaLoading" class="pna-spinner" data-testid="pna-spinner"></div>
              </div>
              <div v-if="!manualAddressMode && pnaError" class="pna-error" data-testid="pna-error">{{ pnaError }}</div>
              <div v-if="!manualAddressMode && pnaInfo.found" class="pna-info-panel" data-testid="pna-info-panel">
                <span class="pna-info-title">Wypełnione z PNA {{ form.postal_code }}</span>
                <span class="pna-info-row">
                  <span class="pna-info-item"><span class="pna-info-label">Gmina:</span> {{ pnaInfo.gmina || '—' }}</span>
                  <span class="pna-info-sep">•</span>
                  <span class="pna-info-item"><span class="pna-info-label">Powiat:</span> {{ pnaInfo.powiat || '—' }}</span>
                  <span class="pna-info-sep">•</span>
                  <span class="pna-info-item"><span class="pna-info-label">Woj:</span> {{ pnaInfo.voivodeship || '—' }}</span>
                </span>
              </div>
              <div class="address-row">
                <textarea v-model="form.delivery_address" @input="onDeliveryAddressInput" class="form-control" rows="2" placeholder="Uwagi dojazdowe (opcjonalnie) — numer działki, bramka, wskazówki dojazdu"></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 3: Warunki finansowe -->
        <div class="page-card" style="margin-bottom:var(--spacing-md);">
          <h3 class="section-title">Warunki finansowe</h3>
          <div class="form-row-4">
            <div class="form-group">
              <label class="form-label">Handlowiec</label>
              <select v-model="form.salesperson_id" class="form-control">
                <option :value="null">— brak —</option>
                <option v-for="sp in settingsStore.salespeople" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Oddział</label>
              <select v-model="form.branch_id" class="form-control">
                <option :value="null">— brak —</option>
                <option v-for="b in settingsStore.branches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" title="Wartość z rozliczenia (suma kosztów klienta z zakładki Rozliczenie)">Wartość z rozliczenia (zł)</label>
              <input :value="settlementTotalFormatted" type="text" class="form-control" disabled style="font-weight:700;" />
            </div>
            <div class="form-group">
              <label class="form-label">Pozostało (zł)</label>
              <input :value="remainingValue" type="text" class="form-control" disabled style="font-weight:700;color:var(--color-error);" />
            </div>
          </div>

          <div class="form-row-4">
            <div class="form-group">
              <label class="form-label">Przedpłata (zł)</label>
              <input v-model.number="form.prepayment_amount" type="number" step="0.01" class="form-control" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label class="form-label">Faktura (zł)</label>
              <input v-model.number="form.invoice_amount" type="number" step="0.01" class="form-control" placeholder="0.00" />
            </div>
          </div>
        </div>

        <!-- Section 4: Kontakt i uwagi -->
        <div class="page-card" style="margin-bottom:var(--spacing-md);">
          <h3 class="section-title">Kontakt i uwagi</h3>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Reprezentowany przez</label>
              <div style="display:flex;gap:8px;">
                <input v-model="form.contact_person1" type="text" class="form-control" placeholder="Imię i nazwisko" />
                <input v-model="form.contact_phone1" type="text" class="form-control" placeholder="Telefon" style="width:140px;" />
                <label class="checkbox-group" style="white-space:nowrap;"><input type="checkbox" v-model="form.show_person1" /> Drukuj</label>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa</label>
              <div style="display:flex;gap:8px;">
                <input v-model="form.contact_person2" type="text" class="form-control" placeholder="Imię i nazwisko" />
                <input v-model="form.contact_phone2" type="text" class="form-control" placeholder="Telefon" style="width:140px;" />
                <label class="checkbox-group" style="white-space:nowrap;"><input type="checkbox" v-model="form.show_person2" /> Drukuj</label>
              </div>
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">E-mail</label>
              <input v-model="form.email" type="email" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Telefon</label>
              <input v-model="form.phone" type="text" class="form-control" />
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Uwagi</label>
              <textarea v-model="form.notes" class="form-control" rows="2"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Opcje</label>
              <div style="display:flex;gap:16px;padding-top:6px;">
                <label class="checkbox-group"><input type="checkbox" v-model="form.hide_delivery_address" /> Ukryj adres dostawy na umowie (klient wpisze ręcznie)</label>
                <label class="checkbox-group"><input type="checkbox" v-model="form.signatures_on_page1" /> Podpisy wymagane na stronie 1</label>
              </div>
            </div>
          </div>
        </div>

        <!-- Positions section — inline editing (RAO-P2-071: zero modali ustawień, tylko ArticlePicker) -->
        <div v-if="isEdit" class="page-card" style="margin-bottom:var(--spacing-md);">
          <div style="display:flex;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
            <span class="section-title" style="margin:0;border:none;">Pozycje umowy</span>
            <span style="font-size:var(--font-size-xs);color:var(--color-text-muted);">Kliknij wiersz aby edytować • Enter = zapisz • Esc = anuluj</span>
            <button class="btn btn-primary btn-sm" style="margin-left:auto;" @click="addPosition">+ Dodaj pozycję</button>
          </div>
          <table class="data-grid">
            <thead>
              <tr>
                <th style="width:32px;">#</th>
                <th>Artykuł</th>
                <th style="width:90px;">Typ najmu</th>
                <th style="width:60px;">Dni</th>
                <th style="width:60px;">Ilość</th>
                <th style="width:110px;">Rozliczanie</th>
                <th>Dostawca</th>
                <th style="width:120px;">Data dost.</th>
                <th style="width:70px;">Warunki</th>
                <th style="width:80px;"></th>
              </tr>
            </thead>
            <tbody>
              <!-- SKELETON LOADER — podczas ładowania pozycji (RAO-P0) -->
              <tr v-if="positionsLoading && !showNewPosRow">
                <td colspan="10" class="empty-state">
                  <span class="skeleton-bar"></span> Ładowanie pozycji…
                </td>
              </tr>
              <!-- EMPTY STATE z CTA — tylko gdy nie ładujemy i nie dodajemy (RAO-P0) -->
              <tr v-else-if="!contractStore.positions.length && !showNewPosRow">
                <td colspan="10" class="empty-state">
                  Brak pozycji na tej umowie. <button class="btn-link" @click="addPosition"><strong>Dodaj pierwszy artykuł</strong></button>
                </td>
              </tr>
              <template v-for="(pos, idx) in contractStore.positions" :key="pos.id">
                <!-- EDIT MODE -->
                <tr v-if="editingPosId === pos.id" class="row-editing">
                  <td>{{ idx + 1 }}</td>
                  <td>
                    <div style="display:flex;align-items:center;gap:4px;">
                      <span style="flex:1;font-size:12px;">{{ editingPosData.article_name || '—' }}</span>
                      <button class="btn-icon" title="Zmień artykuł" @click.stop="reopenArticlePickerForEdit(pos)">✎</button>
                    </div>
                  </td>
                  <td><input v-model="editingPosData.rental_type" type="text" class="form-control form-control-xs" placeholder="—" @keydown.enter="saveInlinePos" @keydown.esc="cancelInlinePos" /></td>
                  <td>
                    <input v-model.number="editingPosData.rental_days" type="number" min="0" class="form-control form-control-xs" :class="{ 'input-error': inlinePosErrors.rental_days }" @keydown.enter="saveInlinePos" @keydown.esc="cancelInlinePos" />
                    <span v-if="inlinePosErrors.rental_days" class="field-error field-error-inline">{{ inlinePosErrors.rental_days }}</span>
                  </td>
                  <td>
                    <input v-model.number="editingPosData.quantity" type="number" min="1" class="form-control form-control-xs" :class="{ 'input-error': inlinePosErrors.quantity }" @keydown.enter="saveInlinePos" @keydown.esc="cancelInlinePos" />
                    <span v-if="inlinePosErrors.quantity" class="field-error field-error-inline">{{ inlinePosErrors.quantity }}</span>
                  </td>
                  <td>
                    <select v-model="editingPosData.billing_frequency" class="form-control form-control-xs">
                      <option :value="null">— brak —</option>
                      <option value="dziennie">dziennie</option>
                      <option value="tygodniowo">tygodniowo</option>
                      <option value="dwutygodniowo">dwutygodniowo</option>
                      <option value="miesięcznie">miesięcznie</option>
                      <option value="godzinowo">godzinowo</option>
                      <option value="jednorazowo">jednorazowo</option>
                    </select>
                  </td>
                  <td>
                    <div style="display:flex;align-items:center;gap:4px;">
                      <span style="flex:1;font-size:12px;">{{ editingPosData.supplier_name || '—' }}</span>
                      <button class="btn-icon" title="Wybierz dostawcę" @click.stop="openSupplierPickerForEdit(pos)">✎</button>
                      <button v-if="editingPosData.supplier_id" class="btn-icon" title="Wyczyść dostawcę" @click.stop="editingPosData.supplier_id = null; editingPosData.supplier_name = ''">✕</button>
                    </div>
                  </td>
                  <td><input v-model="editingPosData.delivery_date" type="date" class="form-control form-control-xs" @keydown.enter="saveInlinePos" @keydown.esc="cancelInlinePos" /></td>
                  <td style="text-align:center;"><span class="badge badge-info">{{ pos.conditions_count || 0 }}</span></td>
                  <td>
                    <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveInlinePos" :disabled="savingPos">✓</button>
                    <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelInlinePos" :disabled="savingPos">✕</button>
                  </td>
                </tr>
                <!-- DISPLAY MODE -->
                <tr v-else :class="{ selected: selectedPosId === pos.id }" @click="selectPosition(pos)" @dblclick="startEditPos(pos)" style="cursor:pointer;">
                  <td>{{ idx + 1 }}</td>
                  <td>{{ pos.article_name }}</td>
                  <td>{{ pos.rental_type || '—' }}</td>
                  <td>{{ pos.rental_days || '—' }}</td>
                  <td>{{ pos.quantity || 1 }}</td>
                  <td>{{ pos.billing_frequency || '—' }}</td>
                  <td>{{ pos.supplier_name || '—' }}</td>
                  <td>{{ pos.delivery_date ? new Date(pos.delivery_date).toLocaleDateString('pl-PL') : '—' }}</td>
                  <td style="text-align:center;"><span class="badge badge-info">{{ pos.conditions_count || 0 }}</span></td>
                  <td>
                    <button class="btn-icon" title="Edytuj" @click.stop="startEditPos(pos)">✎</button>
                    <button class="btn-icon" title="Usuń" @click.stop="deletePosition(pos)">✕</button>
                  </td>
                </tr>
              </template>
              <!-- NEW ROW (po wyborze artykułu z ArticlePicker) -->
              <tr v-if="showNewPosRow" class="row-editing">
                <td>*</td>
                <td>
                  <div style="display:flex;align-items:center;gap:4px;">
                    <span style="flex:1;font-size:12px;font-weight:600;">{{ newPosData.article_name || '—' }}</span>
                    <button class="btn-icon" title="Zmień artykuł" @click.stop="showArticlePicker = true">✎</button>
                  </div>
                </td>
                <td><input ref="newPosRentalTypeInput" v-model="newPosData.rental_type" type="text" class="form-control form-control-xs" placeholder="—" @keydown.enter="saveNewPosRow" @keydown.esc="cancelNewPosRow" /></td>
                <td>
                  <input v-model.number="newPosData.rental_days" type="number" min="0" class="form-control form-control-xs" :class="{ 'input-error': inlinePosErrors.rental_days }" @keydown.enter="saveNewPosRow" @keydown.esc="cancelNewPosRow" />
                  <span v-if="inlinePosErrors.rental_days" class="field-error field-error-inline">{{ inlinePosErrors.rental_days }}</span>
                </td>
                <td>
                  <input v-model.number="newPosData.quantity" type="number" min="1" class="form-control form-control-xs" :class="{ 'input-error': inlinePosErrors.quantity }" @keydown.enter="saveNewPosRow" @keydown.esc="cancelNewPosRow" />
                  <span v-if="inlinePosErrors.quantity" class="field-error field-error-inline">{{ inlinePosErrors.quantity }}</span>
                </td>
                <td>
                  <select v-model="newPosData.billing_frequency" class="form-control form-control-xs">
                    <option :value="null">— brak —</option>
                    <option value="dziennie">dziennie</option>
                    <option value="tygodniowo">tygodniowo</option>
                    <option value="dwutygodniowo">dwutygodniowo</option>
                    <option value="miesięcznie">miesięcznie</option>
                    <option value="godzinowo">godzinowo</option>
                    <option value="jednorazowo">jednorazowo</option>
                  </select>
                </td>
                <td>
                  <div style="display:flex;align-items:center;gap:4px;">
                    <span style="flex:1;font-size:12px;">{{ newPosData.supplier_name || '—' }}</span>
                    <button class="btn-icon" title="Wybierz dostawcę" @click.stop="openSupplierPickerForNew">✎</button>
                    <button v-if="newPosData.supplier_id" class="btn-icon" title="Wyczyść dostawcę" @click.stop="newPosData.supplier_id = null; newPosData.supplier_name = ''">✕</button>
                  </div>
                </td>
                <td><input v-model="newPosData.delivery_date" type="date" class="form-control form-control-xs" @keydown.enter="saveNewPosRow" @keydown.esc="cancelNewPosRow" /></td>
                <td style="text-align:center;"><span class="badge badge-muted">0</span></td>
                <td>
                  <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveNewPosRow" :disabled="savingPos">✓</button>
                  <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelNewPosRow">✕</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Conditions panel for selected position -->
          <ConditionPanel
            v-if="selectedPosId && isEdit"
            :contract-id="Number(props.id)"
            :position-id="selectedPosId"
            :article-id="selectedPositionArticleId"
            :contract-type="form.contract_type"
            @value-changed="onConditionValueChanged"
          />

          <!-- Service fees section -->
        <div v-if="isEdit" class="page-card">
          <div class="fee-header">
            <div class="fee-header-left">
              <span class="section-title" style="margin:0;border:none;">Usługi dodatkowe</span>
              <span class="fee-hint">Kliknij wiersz • Enter = zapisz • Esc = anuluj</span>
            </div>
            <div class="fee-header-right">
              <template v-if="form.contract_type === 'S'">
                <button class="btn btn-secondary btn-sm" @click="applyQuickFeePreset('diesel')" :disabled="!dieselPreset" title="Załaduj zestaw Diesel">
                  Diesel
                </button>
                <button class="btn btn-secondary btn-sm" @click="applyQuickFeePreset('elektryk')" :disabled="!elektrykPreset" title="Załaduj zestaw Elektryk">
                  Elektryk
                </button>
              </template>
              <button class="btn btn-secondary btn-sm" @click="applyQuickFeePreset('default')" :disabled="!defaultPreset" title="Załaduj zestaw domyślny">
                Domyślny
              </button>
              <select v-if="presetPickerList.length" v-model="selectedPresetId" @change="applyPresetWithConfirm" class="form-control form-control-xs" style="width:200px;">
                <option :value="null">Wybierz zestaw…</option>
                <option v-for="p in presetPickerList" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
              <span v-else-if="presetPickerLoading" class="fee-hint">Ładowanie zestawów…</span>
              <span v-else class="fee-hint">Brak zestawów</span>
              <button class="btn btn-secondary btn-sm" @click="resetServiceFees" title="Wyczyść i załaduj domyślny szablon">↻ Reset</button>
              <button class="btn btn-primary btn-sm" @click="addFeeRow">+ Dodaj</button>
            </div>
          </div>
          <table class="data-grid">
            <thead>
              <tr>
                <th style="width:22%;">Nazwa</th>
                <th style="width:9%;">Kwota od</th>
                <th style="width:9%;">Kwota do</th>
                <th style="width:6%;">J.m.</th>
                <th title="Jeśli wypełnione — na PDF drukuje się ten tekst zamiast kwot. Np. „Transport: odbiór własny”, „wycena indywidualna”">Tekst na umowie</th>
                <th style="width:62px;">Aktywna</th>
                <th style="width:56px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!activeServiceFees.length && !showNewFeeRow">
                <td colspan="7" class="empty-state">Brak aktywnych usług dodatkowych — wybierz zestaw lub kliknij „+ Dodaj"</td>
              </tr>
              <template v-for="fee in activeServiceFees" :key="fee.id">
                <!-- EDIT MODE -->
                <tr v-if="editingFeeId === fee.id" class="row-editing">
                  <td>
                    <select v-if="serviceArticles.length" v-model="editingFeeData.article_id" class="form-control form-control-xs" style="margin-bottom:4px;" @change="onEditingServiceArticleSelect">
                      <option :value="null">— wybierz usługę z listy —</option>
                      <option v-for="a in serviceArticles" :key="a.id" :value="a.id">{{ a.name }}{{ a.replacement_value ? ` (${Number(a.replacement_value).toFixed(2)} zł)` : '' }}</option>
                    </select>
                    <input v-model="editingFeeData.name" class="form-control form-control-xs" placeholder="Nazwa usługi" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" />
                  </td>
                  <td><input v-model="editingFeeData.amount_from" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.amount_to" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.description" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td style="text-align:center;"><input type="checkbox" v-model="editingFeeData.is_active" /></td>
                  <td>
                    <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click="saveInlineFee">✓</button>
                    <button class="btn-icon" title="Anuluj (Esc)" @click="cancelInlineFee">✕</button>
                  </td>
                </tr>
                <!-- DISPLAY MODE -->
                <tr v-else @click="startEditFee(fee)" style="cursor:pointer;">
                  <td>{{ fee.name }}</td>
                  <td>{{ fee.amount_from ? Number(fee.amount_from).toFixed(2) + ' zł' : '—' }}</td>
                  <td>{{ fee.amount_to ? Number(fee.amount_to).toFixed(2) + ' zł' : '—' }}</td>
                  <td>{{ fee.unit || '—' }}</td>
                  <td style="font-size:11px;">{{ formatDescription(fee.description, fee.amount_from, fee.amount_to, fee.name) }}</td>
                  <td style="text-align:center;"><span class="badge badge-success">Tak</span></td>
                  <td>
                    <button class="btn-icon" title="Edytuj" @click.stop="startEditFee(fee)">✎</button>
                    <button class="btn-icon" title="Usuń" @click.stop="deleteServiceFee(fee)">✕</button>
                  </td>
                </tr>
              </template>
              <!-- PDF PREVIEW LIVE -->
              <tr v-if="activeServiceFees.length">
                <td colspan="7" class="fee-pdf-preview">
                  <div class="fee-pdf-label">Podgląd PDF:</div>
                  <div class="fee-pdf-list">
                    <div v-for="fee in activeServiceFees" :key="fee.id" class="fee-pdf-line">
                      - {{ formatDescription(fee.description, fee.amount_from, fee.amount_to, fee.name) }}
                    </div>
                  </div>
                </td>
              </tr>
              <!-- NEW ROW -->
              <tr v-if="showNewFeeRow" class="row-editing">
                <td>
                  <select v-if="serviceArticles.length" class="form-control form-control-xs" style="margin-bottom:4px;" @change="onServiceArticleSelect" :value="newFeeData.article_id || ''">
                    <option value="">— wybierz usługę z listy —</option>
                    <option v-for="a in serviceArticles" :key="a.id" :value="a.id">{{ a.name }}{{ a.replacement_value ? ` (${a.replacement_value} zł)` : '' }}</option>
                  </select>
                  <input v-model="newFeeData.name" class="form-control form-control-xs" placeholder="Nazwa usługi" ref="newFeeNameInput" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" />
                </td>
                <td><input v-model="newFeeData.amount_from" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.amount_to" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.description" class="form-control form-control-xs" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td style="text-align:center;"><input type="checkbox" v-model="newFeeData.is_active" /></td>
                <td>
                  <button class="btn-icon" style="color:var(--color-success);" title="Dodaj (Enter)" @click="saveNewFeeRow">✓</button>
                  <button class="btn-icon" title="Anuluj (Esc)" @click="cancelNewFeeRow">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Settlements section (RAO-P1-012 + RAO-P2-022) -->
        <div v-if="isEdit" class="page-card" style="margin-bottom:var(--spacing-md);">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="section-title" style="margin:0;border:none;">Rozliczenie umowy</span>
              <span style="font-size:11px;color:#718096;">Koszt klienta vs koszt firmy</span>
              <!-- RAO-P2-022: status badge -->
              <span v-if="form.is_settled" class="settled-badge-sm">
                ✓ Rozliczona{{ form.settled_at ? ' · ' + new Date(form.settled_at).toLocaleDateString('pl-PL') : '' }}
              </span>
            </div>
            <div style="display:flex;gap:8px;align-items:center;">
              <!-- RAO-P2-022: toggle rozliczenia -->
              <button
                class="btn btn-xs"
                :class="form.is_settled ? 'btn-outline-danger' : 'btn-success'"
                @click="toggleSettled"
                :disabled="settlingContract"
                :title="form.is_settled ? 'Cofnij oznaczenie rozliczona' : 'Oznacz jako rozliczoną'"
              >
                {{ settlingContract ? '...' : (form.is_settled ? '✕ Cofnij rozliczenie' : '✓ Oznacz jako rozliczoną') }}
              </button>
              <button 
                class="btn btn-xs btn-outline"
                @click="toggleFakturowniaPanel"
                :disabled="fakturowniaStore.loading"
              >
                {{ fakturowniaStore.loading ? 'Ładowanie...' : 'Pokaż faktury z FA' }}
              </button>
            </div>
          </div>

          <!-- Fakturownia read-only panel (spike RAO-P2-012) -->
          <div v-if="showFakturowniaPanel" class="page-card" style="margin-bottom:12px;background:#f7fafc;border:1px dashed #cbd5e0;">
            <div style="display:flex;align-items:center;margin-bottom:8px;">
              <span style="font-weight:600;font-size:13px;color:#2d3748;">Faktury z Fakturownia (read-only)</span>
              <button class="btn btn-xs btn-link" style="margin-left:auto;" @click="showFakturowniaPanel = false">Zamknij</button>
            </div>
            <div v-if="fakturowniaStore.error" style="color:#e53e3e;font-size:12px;padding:8px;background:#fff5f5;border-radius:4px;">
              {{ fakturowniaStore.error }}
            </div>
            <div v-else-if="!fakturowniaStore.invoices.length" style="color:#718096;font-size:12px;padding:8px;">
              Brak faktur dla tego kontrahenta (OID: {{ form.contractor_id }})
            </div>
            <div v-else>
              <div v-for="inv in fakturowniaStore.invoices" :key="inv.invoice_number" style="margin-bottom:12px;background:white;padding:8px;border-radius:4px;border:1px solid #e2e8f0;">
                <div style="font-weight:600;font-size:12px;color:#2d3748;margin-bottom:4px;">
                  Faktura {{ inv.invoice_number }} — Netto: {{ Number(inv.total_net).toFixed(2) }} zł
                </div>
                <table style="width:100%;font-size:11px;border-collapse:collapse;">
                  <thead>
                    <tr style="background:#f7fafc;">
                      <th style="text-align:left;padding:4px;">Produkt FA</th>
                      <th style="text-align:right;padding:4px;">Ilość</th>
                      <th style="text-align:right;padding:4px;">Cena netto</th>
                      <th style="text-align:right;padding:4px;">Suma netto</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="line in inv.lines" :key="line.fakturownia_product_id" style="border-bottom:1px solid #edf2f7;">
                      <td style="padding:4px;">{{ line.fakturownia_product_name }}</td>
                      <td style="text-align:right;padding:4px;">{{ line.quantity }}</td>
                      <td style="text-align:right;padding:4px;">{{ Number(line.price_net).toFixed(2) }} zł</td>
                      <td style="text-align:right;padding:4px;">{{ Number(line.total_net).toFixed(2) }} zł</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <table class="data-grid">
            <thead>
              <tr>
                <th>Pozycja</th>
                <th style="width:15%;">Wartość (zł)</th>
                <th style="width:15%;">Koszt firmy (zł)</th>
                <th style="width:12%;">Marża (zł)</th>
                <th>Uwagi</th>
                <th style="width:8%;">Akcja</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!settlements.length">
                <td colspan="6" class="empty-state">
                  <div style="padding: 20px; text-align: center;">
                    <div style="margin-bottom: 12px;">Brak danych rozliczenia — wybierz źródło:</div>
                    <div style="display:flex;gap:10px;justify-content:center;">
                      <button
                        class="btn btn-xs btn-success"
                        @click="initSettlements"
                        :disabled="initializingSettlements"
                      >
                        {{ initializingSettlements ? '...' : '📋 Pobierz z umowy' }}
                      </button>
                      <button
                        class="btn btn-xs btn-primary"
                        @click="initSettlementsFromFakturownia"
                        :disabled="initializingFromFakturownia || !fakturowniaConfigured"
                        :title="!fakturowniaConfigured ? 'Fakturownia nie jest skonfigurowana (Ustawienia → Fakturownia)' : ''"
                      >
                        {{ initializingFromFakturownia ? '...' : '💰 Pobierz z Fakturownia' }}
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
              <tr v-if="settlements.length">
                <td colspan="6" style="padding: 8px; text-align: center;">
                  <button
                    class="btn btn-xs btn-secondary"
                    @click="initSettlements"
                    :disabled="initializingSettlements"
                  >
                    {{ initializingSettlements ? '...' : '🔄 Odśwież z umowy' }}
                  </button>
                  <button
                    class="btn btn-xs btn-danger"
                    @click="clearAllSettlements"
                    :disabled="clearingSettlements"
                    style="margin-left: 8px;"
                  >
                    {{ clearingSettlements ? '...' : '🗑 Wyczyść wszystkie' }}
                  </button>
                </td>
              </tr>
              <tr v-for="s in settlements" :key="s.id">
                <td>{{ getSettlementLabel(s) }}</td>
                <td>
                  <input
                    v-model.number="s.cost_client"
                    type="number"
                    step="0.01"
                    class="form-control form-control-xs"
                    @change="updateSettlement(s)"
                    placeholder="0.00"
                  />
                </td>
                <td>
                  <input
                    v-model.number="s.cost_company"
                    type="number"
                    step="0.01"
                    class="form-control form-control-xs"
                    @change="updateSettlement(s)"
                    placeholder="0.00"
                  />
                </td>
                <td>
                  <span :style="{ color: s.margin > 0 ? 'green' : s.margin < 0 ? 'red' : 'inherit', fontWeight: '600' }">
                    {{ (s.margin !== null && !isNaN(s.margin)) ? Number(s.margin).toFixed(2) + ' zł' : '—' }}
                  </span>
                </td>
                <td>
                  <input
                    v-model="s.notes"
                    type="text"
                    class="form-control form-control-xs"
                    @change="updateSettlement(s)"
                    placeholder="Uwagi..."
                  />
                </td>
                <td style="text-align:center;">
                  <button
                    class="btn btn-xs btn-danger"
                    @click="deleteSettlement(s)"
                    title="Usuń pozycję rozliczenia"
                  >
                    🗑
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    </div>

    <!-- Contractor picker modal -->
    <Transition name="modal">
      <div v-if="showContractorPicker" class="modal-overlay" @click.self="showContractorPicker = false">
        <div class="modal-box" style="min-width:600px;">
          <div class="modal-title">Wybierz kontrahenta</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="pickerSearch" type="text" class="form-control" placeholder="Szukaj..." @input="searchContractors" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <div v-if="!pickerList.length && pickerSearch" class="empty-state" style="padding:32px;text-align:center;color:var(--color-text-muted);">
              Brak wyników dla "{{ pickerSearch }}"
            </div>
            <table v-else class="data-grid">
              <thead><tr><th>Nazwa</th><th>NIP</th><th>Miasto</th></tr></thead>
              <tbody>
                <tr v-for="c in pickerList" :key="c.id" @click="selectContractor(c)" style="cursor:pointer;">
                  <td>{{ c.name }}</td><td>{{ c.nip || '—' }}</td><td>{{ c.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-primary btn-sm" @click="openInlineContractorForm">
              ➕ Dodaj nowego kontrahenta
            </button>
            <button class="btn btn-secondary btn-sm" @click="showContractorPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>
    <!-- Inline contractor form modal - RAO-P2-005 -->
    <Transition name="modal">
      <div v-if="showInlineContractorForm" class="modal-overlay" @click.self="showInlineContractorForm = false">
        <div class="modal-box" style="min-width:700px;max-height:90vh;overflow-y:auto;">
          <div class="modal-title">Nowy kontrahent</div>
          <div v-if="inlineContractorError" style="color:var(--color-danger);font-size:13px;margin-bottom:12px;padding:8px;background:#FED7D7;border-radius:6px;">
            {{ inlineContractorError }}
          </div>
          <div class="form-group">
            <label class="form-label">Pełna nazwa *</label>
            <input v-model="inlineContractorForm.name" type="text" class="form-control" placeholder="Nazwa firmy lub imię i nazwisko" />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Nazwa skrócona</label>
              <input v-model="inlineContractorForm.name_short" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">NIP</label>
              <input v-model="inlineContractorForm.nip" type="text" class="form-control" placeholder="0000000000" maxlength="20" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">REGON</label>
              <input v-model="inlineContractorForm.regon" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">PESEL</label>
              <input v-model="inlineContractorForm.pesel" type="text" class="form-control" />
            </div>
          </div>
          <div style="font-size:13px;font-weight:600;margin:16px 0 8px 0;">Adres główny</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Kod pocztowy</label>
              <input v-model="inlineContractorForm.postal_code" type="text" class="form-control" placeholder="00-000" />
            </div>
            <div class="form-group">
              <label class="form-label">Miejscowość</label>
              <input v-model="inlineContractorForm.city" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Ulica</label>
              <input v-model="inlineContractorForm.street" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Nr lokalu</label>
              <input v-model="inlineContractorForm.unit" type="text" class="form-control" />
            </div>
          </div>
          <div style="font-size:13px;font-weight:600;margin:16px 0 8px 0;">Kontakt</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa 1</label>
              <input v-model="inlineContractorForm.contact_person1" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Telefon 1</label>
              <input v-model="inlineContractorForm.phone1" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa 2</label>
              <input v-model="inlineContractorForm.contact_person2" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Telefon 2</label>
              <input v-model="inlineContractorForm.phone2" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Email</label>
              <input v-model="inlineContractorForm.email" type="email" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Telefon stacjonarny</label>
              <input v-model="inlineContractorForm.landline_phone" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Uwagi</label>
            <textarea v-model="inlineContractorForm.notes" class="form-control" rows="2"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showInlineContractorForm = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="saveInlineContractor" :disabled="savingInlineContractor">
              {{ savingInlineContractor ? '...' : 'Zapisz i wybierz' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>


    <!-- Article picker modal (with availability badge) -->
    <Transition name="modal">
      <div v-if="showArticlePicker" class="modal-overlay" @click.self="showArticlePicker = false">
        <div class="modal-box" style="min-width:650px;">
          <div class="modal-title">Wybierz artykuł</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="articlePickerSearch" type="text" class="form-control" placeholder="Szukaj..." @input="searchArticles" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>Nr rej.</th><th>Marka</th><th>Typ</th><th>Zewnętrzna</th><th>Dostępność</th><th style="width:80px;">Akcje</th></tr></thead>
              <tbody>
                <tr v-if="!articlePickerList.length">
                  <td colspan="7" class="empty-state">Brak wyników dla "{{ articlePickerSearch }}"</td>
                </tr>
                <tr v-for="a in articlePickerList" :key="a.id" style="cursor:pointer;">
                  <td @click="selectArticle(a)">{{ a.name }}</td>
                  <td @click="selectArticle(a)">{{ a.registration_no || '—' }}</td>
                  <td @click="selectArticle(a)">{{ a.brand || '—' }}</td>
                  <td @click="selectArticle(a)"><span :class="['badge', a.is_service ? 'badge-warning' : 'badge-info']">{{ a.is_service ? 'Usługa' : 'Sprzęt' }}</span></td>
                  <td @click="selectArticle(a)" style="text-align:center;">
                    <span v-if="a.is_external" class="badge badge-warning">✓</span>
                    <span v-else class="badge badge-muted">—</span>
                  </td>
                  <td @click="selectArticle(a)">
                    <span v-if="a._avail === true" class="badge badge-success">Wolny</span>
                    <span v-else-if="a._avail === false" class="badge badge-danger">Zajęty</span>
                    <span v-else class="badge badge-muted">—</span>
                  </td>
                  <td>
                    <button class="btn-icon" title="Duplikuj artykuł" @click.stop="duplicateArticle(a)">⧉</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-primary btn-sm" @click="openInlineArticleForm">
              ➕ Dodaj nowy artykuł
            </button>
            <button class="btn btn-secondary btn-sm" @click="showArticlePicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Confirm modal — zastępuje confirm() (RAO-P2-071) -->
    <Transition name="modal">
      <div v-if="confirmState.show" class="modal-overlay" @click.self="cancelConfirm">
        <div class="modal-box" style="max-width:440px;">
          <div class="modal-title">{{ confirmState.title }}</div>
          <p style="margin:12px 0 20px;font-size:14px;line-height:1.5;color:var(--color-text-body);">{{ confirmState.message }}</p>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="cancelConfirm">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="acceptConfirm">{{ confirmState.confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Conflict modal — RAO-P1-023 -->
    <Transition name="modal">
      <div v-if="showConflictModal" class="modal-overlay" @click.self="cancelConflictSelection">
        <div class="modal-box" style="max-width:520px;">
          <div class="modal-title" style="color:var(--color-error);">⚠️ Maszyna zajęta</div>
          <p style="margin:12px 0 8px;">
            <strong>{{ pendingArticle?.name }}</strong> jest przypisana do:
          </p>
          <ul style="margin:0 0 16px 0; padding-left:20px;">
            <li v-for="c in conflictList" :key="c.contract_id" style="margin-bottom:4px;">
              Umowa <strong>{{ c.contract_number }}</strong> — {{ c.contractor_name }}
              <span v-if="c.date_from && c.date_to" style="color:var(--color-text-muted);"> ({{ formatPickerDate(c.date_from) }} – {{ formatPickerDate(c.date_to) }})</span>
            </li>
          </ul>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="cancelConflictSelection">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="confirmConflictSelection">Mimo to dodaj</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Inline article form modal - RAO-P2-006 -->
    <Transition name="modal">
      <div v-if="showInlineArticleForm" class="modal-overlay" @click.self="showInlineArticleForm = false">
        <div class="modal-box" style="min-width:700px;max-height:90vh;overflow-y:auto;">
          <div class="modal-title">Nowy artykuł</div>
          <div v-if="inlineArticleError" style="color:var(--color-danger);font-size:13px;margin-bottom:12px;padding:8px;background:#FED7D7;border-radius:6px;">
            {{ inlineArticleError }}
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Nazwa artykułu *</label>
              <input v-model="inlineArticleForm.name" type="text" class="form-control" placeholder="Np. Koparka gąsienicowa" />
            </div>
            <div class="form-group">
              <label class="form-label">Typ artykułu</label>
              <select v-model="inlineArticleForm.article_type" class="form-control">
                <option value="">— brak —</option>
                <option value="machine">Maszyna</option>
                <option value="vehicle">Pojazd</option>
                <option value="tool">Narzędzie</option>
                <option value="service">Usługa</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-group">
              <input type="checkbox" v-model="inlineArticleForm.is_service" />
              <span>Artykuł jest usługą (nie sprzętem)</span>
            </label>
            <label class="checkbox-group" style="margin-top:6px;">
              <input type="checkbox" v-model="inlineArticleForm.is_external" />
              <span>Maszyna zewnętrzna (nie wliczana do floty własnej)</span>
            </label>
          </div>
          <div class="form-row-2">
            <div class="form-group" v-if="form.contract_type !== 'U'">
              <label class="form-label">Nr wewnętrzny</label>
              <input v-model="inlineArticleForm.internal_number" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Nr rejestracyjny</label>
              <input v-model="inlineArticleForm.registration_no" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Nr seryjny</label>
              <input v-model="inlineArticleForm.serial_no" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Wartość odtworzeniowa (zł)</label>
              <input v-model="inlineArticleForm.replacement_value" type="number" step="0.01" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Marka</label>
              <input v-model="inlineArticleForm.brand" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Model</label>
              <input v-model="inlineArticleForm.model" type="text" class="form-control" />
            </div>
          </div>
          <div style="font-size:13px;font-weight:600;margin:16px 0 8px 0;">Dane techniczne</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Zasięg (m)</label>
              <input v-model.number="inlineArticleForm.zasieg_m" type="number" class="form-control" min="0" step="0.1" placeholder="np. 21.5" />
            </div>
            <div class="form-group">
              <label class="form-label">Udźwig (t)</label>
              <input v-model.number="inlineArticleForm.udzwig_t" type="number" class="form-control" min="0" step="0.1" placeholder="np. 5.0" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Dodatkowe wyposażenie</label>
            <textarea v-model="inlineArticleForm.dodatki" class="form-control" rows="3" placeholder="np. Kosz osobowy, wciągarka..."></textarea>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Kategoria</label>
              <div style="display:flex;flex-direction:column;gap:4px;">
                <select v-model="catSelectedMain" class="form-control" @change="catSelectedSub1 = null; catSelectedSub2 = null">
                  <option :value="null">— brak kategorii —</option>
                  <option v-for="c in catMainOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
                <select v-if="catSub1Options.length" v-model="catSelectedSub1" class="form-control" @change="catSelectedSub2 = null">
                  <option :value="null">— (poziom główny) —</option>
                  <option v-for="c in catSub1Options" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
                <select v-if="catSub2Options.length" v-model="catSelectedSub2" class="form-control">
                  <option :value="null">— (poziom podrzędny) —</option>
                  <option v-for="c in catSub2Options" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Filia</label>
              <select v-model="inlineArticleForm.branch_id" class="form-control">
                <option :value="null">— główna —</option>
                <option v-for="br in settingsStore.branches" :key="br.id" :value="br.id">{{ br.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Min. dni najmu</label>
            <input v-model.number="inlineArticleForm.rental_days" type="number" class="form-control" min="1" />
          </div>
          <div class="form-group">
            <label class="form-label">Opis</label>
            <textarea v-model="inlineArticleForm.description" class="form-control" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Uwagi</label>
            <textarea v-model="inlineArticleForm.notes" class="form-control" rows="2"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showInlineArticleForm = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="saveInlineArticle" :disabled="savingInlineArticle">
              {{ savingInlineArticle ? '...' : 'Zapisz i wybierz' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Supplier picker modal -->
    <Transition name="modal">
      <div v-if="showSupplierPicker" class="modal-overlay" @click.self="showSupplierPicker = false">
        <div class="modal-box" style="min-width:600px;">
          <div class="modal-title">Wybierz dostawcę</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="supplierSearch" type="text" class="form-control" placeholder="Szukaj dostawcy..." @input="searchSuppliers" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>NIP</th><th>Miasto</th></tr></thead>
              <tbody>
                <tr v-for="c in supplierList" :key="c.id" @click="selectSupplier(c)" style="cursor:pointer;">
                  <td>{{ c.name }}</td><td>{{ c.nip || '—' }}</td><td>{{ c.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showSupplierPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useContractStore } from '@/stores/contracts'
import { useContractorStore } from '@/stores/contractors'
import { useArticleStore } from '@/stores/articles'
import { useSettingsStore } from '@/stores/settings'
import { useFakturowniaStore } from '@/stores/fakturownia'
import { useToastStore } from '@/stores/toast'
import ConditionPanel from '@/components/contracts/ConditionPanel.vue'
import ContractPeriodPicker from '@/components/shared/ContractPeriodPicker.vue'
import api from '@/composables/useApi'

const props = defineProps({ id: String })
const router = useRouter()
const route = useRoute()
const contractStore = useContractStore()
const contractorStore = useContractorStore()
const articleStore = useArticleStore()
const settingsStore = useSettingsStore()
const fakturowniaStore = useFakturowniaStore()
const toastStore = useToastStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const selectedPosId = ref(null)

const form = ref({
  contractor_id: null, branch_id: null, salesperson_id: null,
  contract_type: 'S', oid: null, delivery_address: '', postal_code: '', city: '', latitude: null, longitude: null, date_from: '', date_to: '',
  // RAO-P1-021/P2-033: total_value usunięte (martwe pole)
  prepayment_amount: 0, prepayment_document: '',
  invoice_amount: 0, invoice_document: '', notes: '',
  contact_person1: '', contact_phone1: '', show_person1: true,
  contact_person2: '', contact_phone2: '', show_person2: true,
  email: '', phone: '', contractor_name: '', working_days_per_week: 6, report_without_data: false, hide_delivery_address: false, signatures_on_page1: false,
  is_settled: false, settled_at: null,  // RAO-P2-022
})

// RAO-P1-021: Wartość umowy z rozliczenia (suma cost_client z settlements)
// Pole "Wartość (zł)" w formularzu jest read-only — wartość pochodzi z rozliczenia
const settlementTotalValue = computed(() => {
  if (!settlements.value.length) return 0
  return settlements.value.reduce((sum, s) => sum + (Number(s.cost_client) || 0), 0)
})

const settlementTotalFormatted = computed(() => {
  if (!settlements.value.length) return '— rozlicz umowę'
  return settlementTotalValue.value.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
})

const remainingValue = computed(() => {
  // RAO-P1-021/P2-033: użyj wartości z rozliczenia (total_value usunięte)
  const total = settlements.value.length ? settlementTotalValue.value : 0
  const pre = Number(form.value.prepayment_amount) || 0
  const inv = Number(form.value.invoice_amount) || 0
  const remaining = total - pre - inv
  return remaining.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
})

// RAO-P1-100: artykuł wybranej pozycji dla ConditionPanel (cennik / ostatnia umowa)
const selectedPositionArticleId = computed(() => {
  const pos = contractStore.positions.find(p => p.id === selectedPosId.value)
  return pos?.article_id ?? null
})

// RAO-P1-100: grid usług pokazuje tylko aktywne pozycje
const activeServiceFees = computed(() =>
  (contractStore.serviceFees || []).filter(f => f.is_active)
)

const contractorName = ref('')
interface ContractorAddress {
  id: number
  name?: string | null
  city?: string | null
  street?: string | null
  postal_code?: string | null
}
const contractorAddresses = ref<ContractorAddress[]>([])
const selectedAddressId = ref<number | null>(null)
const showContractorPicker = ref(false)
const pickerSearch = ref('')
interface ContractorPick { id: number; name: string; nip?: string | null; city?: string | null }
const pickerList = ref<ContractorPick[]>([])

// RAO-P2-005: Inline contractor creation
const showInlineContractorForm = ref(false)
const savingInlineContractor = ref(false)
const inlineContractorError = ref('')
const inlineContractorForm = ref({
  name: '', name_short: '', nip: '', regon: '', pesel: '',
  postal_code: '', city: '', street: '', unit: '', notes: '',
  email: '', contact_person1: '', phone1: '',
  contact_person2: '', phone2: '', landline_phone: '', website: '',
})

// RAO-P2-006: Inline article creation
const showInlineArticleForm = ref(false)
const savingInlineArticle = ref(false)
const inlineArticleError = ref('')
const inlineArticleForm = ref({
  name: '', is_service: false, internal_number: '', registration_no: '',
  serial_no: '', brand: '', model: '', replacement_value: null,
  category_id: null, owner_id: null, branch_id: null,
  description: '', notes: '', rental_days: null, article_type: '',
  zasieg_m: null, udzwig_t: null, dodatki: null,
  is_archival: false, is_external: false,
})
// Category cascade for inline article form
const catSelectedMain = ref(null)
const catSelectedSub1 = ref(null)
const catSelectedSub2 = ref(null)

// RAO-P2-012 spike: Fakturownia panel
const showFakturowniaPanel = ref(false)

async function toggleFakturowniaPanel() {
  if (showFakturowniaPanel.value) {
    showFakturowniaPanel.value = false
    return
  }
  showFakturowniaPanel.value = true
  await fakturowniaStore.fetchInvoicesByContractId(Number(props.id))
}

// RAO-P1-008: Auto-fill city from postal code + panel PNA (gmina/powiat/wojewodztwo)
const pnaLoading = ref(false)
const pnaError = ref<string | null>(null)
const pnaInfo = ref<{ city: string; gmina: string | null; powiat: string | null; voivodeship: string | null; found: boolean }>({
  city: '', gmina: null, powiat: null, voivodeship: null, found: false,
})
const manualAddressMode = ref(false)  // P1-002: ręczny adres (wyłącz auto-fill)

const onPostalCodeBlur = async () => {
  if (manualAddressMode.value) return  // P1-002: skip auto-fill w trybie ręcznym
  const code = form.value.postal_code.trim()
  // Reset state on every blur
  pnaError.value = null
  if (!code || code.length !== 6) {
    pnaInfo.value = { city: '', gmina: null, powiat: null, voivodeship: null, found: false }
    return
  }
  await lookupPna(code)
}

// RAO-P2-028: Reusable PNA lookup — wywoływane z onPostalCodeBlur, onDeliveryAddressInput, onAddressSelect
const lookupPna = async (code: string, opts?: { fillCity?: boolean }) => {
  const fillCity = opts?.fillCity ?? true
  pnaError.value = null
  if (!code || code.length !== 6) {
    pnaInfo.value = { city: '', gmina: null, powiat: null, voivodeship: null, found: false }
    return
  }
  pnaLoading.value = true
  try {
    const { data } = await api.get(`/integrations/postal-codes/${encodeURIComponent(code)}`)
    // Auto-fill city (sugestia — pole edytowalne, pomijaj gdy użytkownik ręcznie zmienił)
    if (fillCity && data.city && !cityManuallyEdited) {
      form.value.city = data.city
    }
    pnaInfo.value = {
      city: data.city ?? '',
      gmina: data.gmina ?? null,
      powiat: data.powiat ?? null,
      voivodeship: data.voivodeship ?? null,
      found: true,
    }
  } catch (error: any) {
    if (error?.response?.status === 404) {
      pnaError.value = `Nie znaleziono kodu ${code} w bazie. Wpisz miasto ręcznie.`
    } else {
      pnaError.value = 'Nie udało się pobrać danych PNA. Wpisz miasto ręcznie.'
    }
    pnaInfo.value = { city: '', gmina: null, powiat: null, voivodeship: null, found: false }
  } finally {
    pnaLoading.value = false
  }
}

// RAO-P1-017: Auto-fill city + postal_code from delivery_address (hybrid: offline + Nominatim)
let deliveryAddressTimer: ReturnType<typeof setTimeout> | null = null
let deliveryAddressAbort: AbortController | null = null
let cityManuallyEdited = false
let postalManuallyEdited = false

const onCityInput = () => { cityManuallyEdited = true }
const onPostalInput = () => { postalManuallyEdited = true }

const onDeliveryAddressInput = () => {
  if (manualAddressMode.value) return  // P1-002: skip auto-fill w trybie ręcznym
  if (deliveryAddressTimer) clearTimeout(deliveryAddressTimer)
  deliveryAddressTimer = setTimeout(async () => {
    const addr = form.value.delivery_address?.trim()
    if (!addr || addr.length < 5) return  // too short, skip
    // Cancel previous in-flight request (race condition guard)
    if (deliveryAddressAbort) deliveryAddressAbort.abort()
    deliveryAddressAbort = new AbortController()
    try {
      // Hybrid endpoint: offline regex first, Nominatim fallback
      const { data } = await api.post('/integrations/extract-address', { address: addr }, { signal: deliveryAddressAbort.signal })
      // Only fill if user hasn't manually edited these fields
      if (data.city && !cityManuallyEdited) form.value.city = data.city
      if (data.postal_code && !postalManuallyEdited) form.value.postal_code = data.postal_code
      if (data.lat && data.lon) {
        form.value.latitude = data.lat
        form.value.longitude = data.lon
      }
      // RAO-P2-028: Auto-trigger PNA lookup po extract-address — panel gmina/powiat/woj od razu
      if (data.postal_code && data.postal_code.length === 6 && !postalManuallyEdited) {
        await lookupPna(data.postal_code, { fillCity: !cityManuallyEdited })
      }
    } catch (e: any) {
      // AbortError is expected when canceling previous request
      if (e?.name !== 'AbortError') {
        // Silently fail — Nominatim may not find the address
      }
    }
  }, 800)  // 800ms debounce
}

onUnmounted(() => {
  if (deliveryAddressTimer) clearTimeout(deliveryAddressTimer)
  if (deliveryAddressAbort) deliveryAddressAbort.abort()
  // RAO-P1-043: cleanup timerów pickerów — zapobiega memory leakom
  if (pickerTimer) clearTimeout(pickerTimer)
  if (artTimer) clearTimeout(artTimer)
  if (supTimer) clearTimeout(supTimer)
})

// RAO-P2-071: Inline editing pozycji — zero modali ustawień, tylko ArticlePicker
// Pattern skopiowany z Service Fees (editingFeeId / editingFeeData / startEditFee / saveInlineFee)
interface PosInlineData {
  article_id: number | null
  article_name: string
  rental_type: string | null
  rental_days: number | null
  quantity: number
  unit_price: number | null
  costs: number | null
  rate_type_id: number | null
  billing_frequency: string | null
  billing_unit: string | null
  supplier_id: number | null
  supplier_name: string
  delivery_date: string | null
  description: string | null
}
const editingPosId = ref<number | null>(null)
const editingPosData = ref<PosInlineData>(emptyPosData())
const showNewPosRow = ref(false)
const newPosData = ref<PosInlineData>(emptyPosData())
const newPosRentalTypeInput = ref<HTMLInputElement | null>(null)
const savingPos = ref(false)
// RAO-P0: flaga ładowania pozycji — skeleton loader zamiast mylącego empty state
const positionsLoading = ref(false)
// RAO-P0: błędy walidacji inline (quantity ≥ 1, rental_days ≥ 0)
const inlinePosErrors = ref<{ quantity?: string; rental_days?: string }>({})

function clearInlinePosErrors() {
  inlinePosErrors.value = {}
}

// RAO-P0: walidacja inline przed zapisem — zwraca true jeśli OK, false jeśli błąd (ustawia inlinePosErrors)
function validatePosInline(d: PosInlineData): boolean {
  clearInlinePosErrors()
  let ok = true
  // quantity: ≥ 1, nie NaN (puste pole z v-model.number daje '' → NaN/undefined)
  const q = d.quantity
  if (q == null || Number.isNaN(q) || q < 1) {
    inlinePosErrors.value.quantity = 'Ilość musi być ≥ 1'
    ok = false
  }
  // rental_days: ≥ 0 jeśli podane (może być null = brak)
  const rd = d.rental_days
  if (rd != null && !Number.isNaN(rd) && rd < 0) {
    inlinePosErrors.value.rental_days = 'Dni nie mogą być ujemne'
    ok = false
  }
  return ok
}
// Tryb wyboru artykułu: 'new' | 'edit' — determinuje cel po wyborze z ArticlePicker
const articlePickerMode = ref<'new' | 'edit'>('new')
const showArticlePicker = ref(false)
const articlePickerSearch = ref('')
const articlePickerList = ref([])

function emptyPosData(): PosInlineData {
  return {
    article_id: null, article_name: '', rental_type: null, rental_days: null,
    quantity: 1, unit_price: null, costs: null, rate_type_id: null,
    billing_frequency: null, billing_unit: null, supplier_id: null,
    supplier_name: '', delivery_date: null, description: null,
  }
}

// RAO-P2-071: Confirm modal — zastępuje confirm() w całym komponencie
const confirmState = ref<{
  show: boolean
  title: string
  message: string
  confirmText: string
  onConfirm: (() => void) | null
}>({ show: false, title: '', message: '', confirmText: 'Potwierdź', onConfirm: null })

function requestConfirm(message: string, onConfirm: () => void, title = 'Potwierdzenie', confirmText = 'Potwierdź') {
  confirmState.value = { show: true, title, message, confirmText, onConfirm }
}
function acceptConfirm() {
  const fn = confirmState.value.onConfirm
  confirmState.value = { show: false, title: '', message: '', confirmText: 'Potwierdź', onConfirm: null }
  fn?.()
}
function cancelConfirm() {
  confirmState.value = { show: false, title: '', message: '', confirmText: 'Potwierdź', onConfirm: null }
}

// RAO-P2-006: Category cascade computed properties for inline article form
const catMainOptions = computed(() => settingsStore.categoriesTree)
const catSub1Options = computed(() => {
  if (!catSelectedMain.value) return []
  return catMainOptions.value.find(c => c.id === catSelectedMain.value)?.children || []
})
const catSub2Options = computed(() => {
  if (!catSelectedSub1.value) return []
  return catSub1Options.value.find(c => c.id === catSelectedSub1.value)?.children || []
})

// Update form.category_id when cascade changes
watch([catSelectedMain, catSelectedSub1, catSelectedSub2], () => {
  inlineArticleForm.value.category_id = catSelectedSub2.value ?? catSelectedSub1.value ?? catSelectedMain.value
})

// Helper: find path from root to node
function findCatPath(tree, id, path) {
  if (!path) path = []
  for (const node of tree) {
    const newPath = [...path, node]
    if (node.id === id) return newPath
    if (node.children?.length) {
      const found = findCatPath(node.children, id, newPath)
      if (found) return found
    }
  }
  return null
}

// Set cascade from category_id
function setCategoryFromId(categoryId) {
  if (!categoryId || !settingsStore.categoriesTree.length) {
    catSelectedMain.value = null
    catSelectedSub1.value = null
    catSelectedSub2.value = null
    return
  }
  const path = findCatPath(settingsStore.categoriesTree, categoryId)
  if (!path) return
  catSelectedMain.value = path[0]?.id || null
  catSelectedSub1.value = path[1]?.id || null
  catSelectedSub2.value = path[2]?.id || null
}

// RAO-P1-023: conflict modal state
interface ConflictingContract {
  contract_id: number
  contract_number: string
  contractor_name: string
  date_from: string | null
  date_to: string | null
}
// RAO-P2-066: konflikt z rezerwacją maszyny (article_reservations)
interface ConflictingReservation {
  reservation_id: number
  reserved_from: string
  reserved_to: string
  note: string | null
  available_from: string | null
}
interface AvailabilityResponse {
  is_available: boolean
  conflicting_contracts: ConflictingContract[]
  conflicting_reservations: ConflictingReservation[]
}
interface ArticlePickerItem {
  id: number
  name: string
  is_service: boolean
  [key: string]: unknown
}
const showConflictModal = ref(false)
const conflictList = ref<ConflictingContract[]>([])
// RAO-P2-066: konflikty z rezerwacjami (osobna lista, renderowana w modalu)
const reservationConflictList = ref<ConflictingReservation[]>([])
const pendingArticle = ref<ArticlePickerItem | null>(null)

const supplierName = ref('')
const showSupplierPicker = ref(false)
const supplierSearch = ref('')
const supplierList = ref([])

interface FeeData {
  name: string
  amount_from: number | null
  amount_to: number | null
  unit: string
  description: string
  is_active: boolean
  article_id?: number | null  // RAO-P2-059
  default_price?: number | null  // RAO-P2-059
}
const editingFeeId = ref<number | null>(null)
const editingFeeData = ref<Partial<FeeData>>({})
const showNewFeeRow = ref(false)
const newFeeData = ref<FeeData>({ name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true, article_id: null, default_price: null })
const newFeeNameInput = ref(null)

// RAO-P2-059: ArticlePicker dla usług dodatkowych
const serviceArticles = ref<any[]>([])
async function fetchServiceArticles() {
  try {
    const { data } = await api.get('/articles', { params: { is_service: true, per_page: 100 } })
    serviceArticles.value = data.items || []
  } catch { serviceArticles.value = [] }
}
function onServiceArticleSelect(event: Event) {
  const select = event.target as HTMLSelectElement
  const articleId = Number(select.value)
  if (!articleId) {
    newFeeData.value.article_id = null
    newFeeData.value.default_price = null
    return
  }
  const article = serviceArticles.value.find(a => a.id === articleId)
  if (article) {
    newFeeData.value.article_id = article.id
    newFeeData.value.name = article.name
    const price = article.replacement_value ? Number(article.replacement_value) : null
    newFeeData.value.default_price = price
    if (price !== null && newFeeData.value.amount_from === null) {
      newFeeData.value.amount_from = price
    }
  }
}

function onEditingServiceArticleSelect(event: Event) {
  const select = event.target as HTMLSelectElement
  const articleId = Number(select.value)
  if (!articleId) {
    editingFeeData.value.article_id = null
    editingFeeData.value.default_price = null
    return
  }
  const article = serviceArticles.value.find(a => a.id === articleId)
  if (article) {
    editingFeeData.value.article_id = article.id
    editingFeeData.value.name = article.name
    const price = article.replacement_value ? Number(article.replacement_value) : null
    editingFeeData.value.default_price = price
    if (price !== null && editingFeeData.value.amount_from === null) {
      editingFeeData.value.amount_from = price
    }
  }
}

// RAO-P1-012: Settlements
interface Settlement {
  id: number
  cost_client: number | null
  cost_company: number | null
  margin: number | null
  notes: string | null
  service_fee_id?: number | null
  service_fee_name?: string | null
}
const settlements = ref<Settlement[]>([])
const initializingSettlements = ref(false)
const initializingFromFakturownia = ref(false)

// RAO-P2-012: Fakturownia configuration check
const fakturowniaConfigured = computed(() => {
  const s = fakturowniaStore.settings
  return s && s.enabled && s.domain_subdomain && s.api_token_preview
})


// Format description with actual amounts instead of placeholders
// Format: "{name}: {amount_from} zł - {amount_to} zł" or "{name}: {amount_from} zł ({description})"
function formatDescription(description, amount_from, amount_to, name = '') {
  if (!description) {
    // If no description, format amounts directly
    if (amount_from !== null && amount_from !== undefined) {
      const formattedFrom = Number(amount_from).toLocaleString('pl-PL', { minimumFractionDigits: 2 })
      if (amount_to !== null && amount_to !== undefined) {
        const formattedTo = Number(amount_to).toLocaleString('pl-PL', { minimumFractionDigits: 2 })
        const prefix = name ? `${name}: ` : ''
        return `${prefix}${formattedFrom} zł - ${formattedTo} zł`
      }
      const prefix = name ? `${name}: ` : ''
      return `${prefix}${formattedFrom} zł`
    }
    return name ? `${name}: wycena indywidualna` : '—'
  }

  // If description exists, replace $1/$2 placeholders with actual amounts
  let result = description
  if (amount_from !== null && amount_from !== undefined) {
    const formattedFrom = Number(amount_from).toLocaleString('pl-PL', { minimumFractionDigits: 2 })
    result = result.replace(/\$1/g, formattedFrom + ' zł')
  }
  if (amount_to !== null && amount_to !== undefined) {
    const formattedTo = Number(amount_to).toLocaleString('pl-PL', { minimumFractionDigits: 2 })
    result = result.replace(/\$2/g, formattedTo + ' zł')
  }
  const prefix = name ? `${name}: ` : ''
  return `${prefix}${result}`
}

onMounted(async () => {
  await Promise.all([
    settingsStore.fetchSalespeople(),
    settingsStore.fetchBranches(),
    settingsStore.fetchRateTypes(),
    settingsStore.fetchCategoriesTree(), // RAO-P2-006: Load categories for inline article form
    fakturowniaStore.fetchSettings(),
    fetchServiceArticles(), // RAO-P2-059: Load service articles for fee picker
  ])

  const [ctRes, artRes] = await Promise.allSettled([
    api.get('/contractors', { params: { per_page: 30 } }),
    api.get('/articles', { params: { per_page: 50, is_service: form.value.contract_type === 'U' ? true : false } }),
  ])
  if (ctRes.status === 'fulfilled') pickerList.value = ctRes.value.data.items
  if (artRes.status === 'fulfilled') articlePickerList.value = artRes.value.data.items

  const contractorIdFromQuery = route.query.contractor_id
  if (contractorIdFromQuery) {
    const ct = await contractorStore.fetchOne(Number(contractorIdFromQuery))
    form.value.contractor_id = ct.id
    contractorName.value = ct.name
    form.value.contractor_name = ct.name
    await loadContractorAddresses(ct.id)
  }

  if (isEdit.value) {
    loading.value = true
    try {
      const data = await contractStore.fetchOne(Number(props.id))
      Object.assign(form.value, data)
      if (data.contractor_id) {
        try {
          const ct = await contractorStore.fetchOne(data.contractor_id)
          contractorName.value = ct.name
          await loadContractorAddresses(data.contractor_id)
        } catch {}
      }
      // RAO-P0: skeleton loader podczas ładowania pozycji (zamiast mylącego empty state)
      positionsLoading.value = true
      try {
        await contractStore.fetchPositions(Number(props.id))
      } finally {
        positionsLoading.value = false
      }
      await contractStore.fetchServiceFees(Number(props.id))
      await fetchSettlements(Number(props.id))
    } finally {
      loading.value = false
    }
  }
})

async function loadContractorAddresses(contractorId) {
  try {
    const { data } = await api.get(`/contractors/${contractorId}/addresses`)
    contractorAddresses.value = data
  } catch { contractorAddresses.value = [] }
}

async function onAddressSelect() {
  const addr = contractorAddresses.value.find(a => a.id === selectedAddressId.value)
  if (addr) {
    const parts = [addr.street, addr.postal_code, addr.city].filter(Boolean)
    form.value.delivery_address = parts.join(', ')
    // RAO-P2-028: Auto-wypełnij postal_code + city z adresu kontrahenta
    // Reset flag ręcznej edycji — to auto-fill z listy, nie ręczna zmiana
    if (addr.postal_code) {
      form.value.postal_code = addr.postal_code
      postalManuallyEdited = false
    }
    if (addr.city) {
      form.value.city = addr.city
      cityManuallyEdited = false
    }
    // RAO-P2-028: Auto-trigger PNA lookup — panel gmina/powiat/woj od razu
    if (addr.postal_code && addr.postal_code.length === 6) {
      await lookupPna(addr.postal_code, { fillCity: !addr.city })
    }
    // RAO-P2-005: geocode address to get lat/lng
    try {
      const addressStr = parts.join(', ')
      const { data } = await api.post('/integrations/geocode', { address: addressStr })
      if (data.lat && data.lon) {
        form.value.latitude = data.lat
        form.value.longitude = data.lon
      }
    } catch {
      // Silently fail if geocoding fails
    }
  }
}

function goBack() { router.push('/dashboard/contracts') }

function buildPayload() {
  const v = { ...form.value }
  const dateFields = ['date_from', 'date_to']
  const nullableStr = ['delivery_address', 'prepayment_document', 'invoice_document',
    'notes', 'contact_person1', 'contact_phone1', 'contact_person2', 'contact_phone2',
    'email', 'phone', 'contractor_name']
  dateFields.forEach(f => { if (!v[f]) v[f] = null })
  nullableStr.forEach(f => { if (v[f] === '') v[f] = null })
  return v
}

async function handleSave() {
  if (!form.value.contractor_id) { errorMsg.value = 'Wybierz kontrahenta'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    const payload = buildPayload()
    if (isEdit.value) {
      await contractStore.update(Number(props.id), payload)
    } else {
      const result = await contractStore.create(payload)
      router.push(`/contracts/${result.id}/edit`)
    }
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      // Parsuj błędy walidacji Pydantic
      const errorMessages = detail.map((err: any) => {
        const field = err.loc?.[1] || err.loc?.[0] || 'pole'
        const msg = err.msg || 'Błąd walidacji'
        // Mapowanie nazw pól na polski
        const fieldMap: Record<string, string> = {
          postal_code: 'Kod pocztowy',
          city: 'Miasto',
          date_from: 'Data od',
          date_to: 'Data do',
          contractor_id: 'Kontrahent'
        }
        const polishField = fieldMap[field] || field
        return `${polishField}: ${msg}`
      })
      errorMsg.value = errorMessages.join(', ')
    } else {
      errorMsg.value = detail || 'Błąd zapisu'
    }
  } finally {
    saving.value = false
  }
}

async function recalcTotal() {
  if (!isEdit.value) return
  try {
    // RAO-P1-021/P2-033: nie zapisujemy total_value (usunięte), tylko odświeżamy settlements
    await api.post(`/contracts/${props.id}/recalculate`)
    await contractStore.fetchOne(Number(props.id))
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd kalkulacji')
  }
}

async function handleFakturownia() {
  if (!isEdit.value) return
  if (!contractStore.current?.id) return
  try {
    await fakturowniaStore.fetchInvoicesByContractId(contractStore.current.id)
    if (fakturowniaStore.invoices.length > 0) {
      const total = fakturowniaStore.invoices.reduce((sum, inv) => sum + inv.total_net, 0)
      toastStore.info(`Pobrano ${fakturowniaStore.invoices.length} faktur o łącznej kwocie ${total.toFixed(2)} zł`)
    } else {
      toastStore.info('Brak faktur dla tej umowy')
    }
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd pobierania faktur z Fakturownia')
  }
}

async function generateReport(type) {
  if (!isEdit.value) return
  try {
    await contractStore.generateReport(Number(props.id), type)
  } catch (e) {
    toastStore.error('Błąd generowania raportu')
  }
}

// RAO-P2-022: Settle / unsettle contract
const settlingContract = ref(false)
async function toggleSettled() {
  if (!props.id) return
  settlingContract.value = true
  try {
    const newVal = !form.value.is_settled
    const { data } = await api.patch(`/contracts/${props.id}/settle`, { is_settled: newVal })
    form.value.is_settled = data.is_settled
    form.value.settled_at = data.settled_at
    await nextTick() // Force Vue re-render
  } catch (e: any) {
    toastStore.error('Błąd zmiany statusu rozliczenia: ' + (e.response?.data?.detail || e.message))
  } finally {
    settlingContract.value = false
  }
}

// RAO-P1-012: Settlement functions
async function fetchSettlements(contractId) {
  try {
    const { data } = await api.get(`/settlements/contract/${contractId}`)
    settlements.value = data
  } catch (e) {
    console.error('Failed to fetch settlements:', e)
    settlements.value = []
  }
}

function getSettlementLabel(s: any) {
  // RAO-P2-012: Usługi dodatkowe mają service_fee_id + service_fee_name z backend
  if (s.service_fee_id) {
    return s.service_fee_name || `Usługa dodatkowa #${s.service_fee_id}`
  }
  // Pozycja umowy (maszyna/sprzęt)
  if (s.position_id) {
    const pos = contractStore.positions.find(p => p.id === s.position_id)
    if (pos) return pos.article_name || `Pozycja #${s.position_id}`
    return `Pozycja #${s.position_id}`
  }
  // RAO-P0-013: Unmapped FA settlements — użyj article_name_snapshot z faktury
  if (s.article_name_snapshot) {
    return s.article_name_snapshot
  }
  return '—'
}

async function updateSettlement(settlement) {
  try {
    await api.put(`/settlements/${settlement.id}`, {
      cost_client: settlement.cost_client,
      cost_company: settlement.cost_company,
      notes: settlement.notes
    })
    // Re-fetch to get updated margin
    await fetchSettlements(Number(props.id))
  } catch (e) {
    toastStore.error('Błąd aktualizacji rozliczenia')
    // Revert to original values
    await fetchSettlements(Number(props.id))
  }
}

// RAO-P0-013: Delete single settlement + clear all
const clearingSettlements = ref(false)

async function deleteSettlement(settlement) {
  requestConfirm(
    `Usunąć pozycję rozliczenia „${getSettlementLabel(settlement)}"?`,
    async () => {
      try {
        await api.delete(`/settlements/${settlement.id}`)
        await fetchSettlements(Number(props.id))
        toastStore.success('Pozycja rozliczenia usunięta')
      } catch (e: any) {
        toastStore.error('Błąd usuwania rozliczenia: ' + (e.response?.data?.detail || e.message))
      }
    },
    'Usuń pozycję rozliczenia',
    'Usuń',
  )
}

async function clearAllSettlements() {
  if (!settlements.value.length) return
  requestConfirm(
    `Usunąć WSZYSTKIE pozycje rozliczenia (${settlements.value.length})? Tej operacji nie można cofnąć.`,
    async () => {
      clearingSettlements.value = true
      try {
        await api.delete(`/settlements/contract/${props.id}/all`)
        await fetchSettlements(Number(props.id))
        toastStore.success('Rozliczenia wyczyszczone')
      } catch (e: any) {
        toastStore.error('Błąd czyszczenia rozliczeń: ' + (e.response?.data?.detail || e.message))
      } finally {
        clearingSettlements.value = false
      }
    },
    'Wyczyść rozliczenia',
    'Usuń wszystkie',
  )
}

async function initSettlements() {
  if (!props.id) return
  initializingSettlements.value = true
  try {
    const { data } = await api.post(`/settlements/contract/${props.id}/init`)
    settlements.value = data
    toastStore.success('Rozliczenie zainicjowane')
  } catch (e: any) {
    toastStore.error('Błąd inicjalizacji rozliczenia: ' + (e.response?.data?.detail || e.message))
  } finally {
    initializingSettlements.value = false
  }
}

async function initSettlementsFromFakturownia() {
  if (!props.id) return
  initializingFromFakturownia.value = true
  try {
    const { data } = await api.post(`/settlements/contract/${props.id}/init-from-fakturownia`)
    settlements.value = data
    toastStore.success('Rozliczenie zainicjowane z Fakturownia')
  } catch (e: any) {
    toastStore.error('Błąd pobierania z Fakturownia: ' + (e.response?.data?.detail || e.message))
  } finally {
    initializingFromFakturownia.value = false
  }
}

let pickerTimer: ReturnType<typeof setTimeout> | null = null
async function searchContractors() {
  if (pickerTimer) clearTimeout(pickerTimer)
  pickerTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: pickerSearch.value, per_page: 30 } })
    pickerList.value = data.items
  }, 300)
}

async function selectContractor(c) {
  form.value.contractor_id = c.id
  form.value.contractor_name = c.name
  contractorName.value = c.name
  showContractorPicker.value = false
  selectedAddressId.value = null
  await loadContractorAddresses(c.id)
}

// RAO-P2-005: Inline contractor creation functions
function openInlineContractorForm() {
  showInlineContractorForm.value = true
  inlineContractorError.value = ''
  // Pre-fill with search term if it looks like a name
  if (pickerSearch.value && pickerSearch.value.length > 2 && isNaN(Number(pickerSearch.value))) {
    inlineContractorForm.value.name = pickerSearch.value
  }
}

async function saveInlineContractor() {
  savingInlineContractor.value = true
  inlineContractorError.value = ''
  
  // Basic validation
  if (!inlineContractorForm.value.name || !inlineContractorForm.value.name.trim()) {
    inlineContractorError.value = 'Podaj nazwę kontrahenta'
    savingInlineContractor.value = false
    return
  }
  
  try {
    const result = await contractorStore.create(inlineContractorForm.value)
    // Add to picker list
    pickerList.value.unshift(result)
    // Auto-select the new contractor
    await selectContractor(result)
    // Close the inline form
    showInlineContractorForm.value = false
    // Reset the form
    inlineContractorForm.value = {
      name: '', name_short: '', nip: '', regon: '', pesel: '',
      postal_code: '', city: '', street: '', unit: '', notes: '',
      email: '', contact_person1: '', phone1: '',
      contact_person2: '', phone2: '', landline_phone: '', website: '',
    }
  } catch (e: any) {
    inlineContractorError.value = e?.response?.data?.detail || 'Błąd zapisu kontrahenta'
  } finally {
    savingInlineContractor.value = false
  }
}

// RAO-P2-006: Inline article creation functions
function openInlineArticleForm() {
  showInlineArticleForm.value = true
  inlineArticleError.value = ''
  // Pre-fill with search term if it looks like a name
  if (articlePickerSearch.value && articlePickerSearch.value.length > 2 && isNaN(Number(articlePickerSearch.value))) {
    inlineArticleForm.value.name = articlePickerSearch.value
  }
  // Pre-fill is_service based on contract type
  inlineArticleForm.value.is_service = form.value.contract_type === 'U'
  // Reset category cascade
  catSelectedMain.value = null
  catSelectedSub1.value = null
  catSelectedSub2.value = null
}

async function saveInlineArticle() {
  savingInlineArticle.value = true
  inlineArticleError.value = ''

  // Basic validation
  if (!inlineArticleForm.value.name || !inlineArticleForm.value.name.trim()) {
    inlineArticleError.value = 'Podaj nazwę artykułu'
    savingInlineArticle.value = false
    return
  }

  try {
    const payload = { ...inlineArticleForm.value }
    // Clean up null values
    if (!payload.replacement_value) payload.replacement_value = null
    if (!payload.rental_days) payload.rental_days = null
    if (!payload.article_type) payload.article_type = null
    if (!payload.zasieg_m) payload.zasieg_m = null
    if (!payload.udzwig_t) payload.udzwig_t = null
    if (!payload.dodatki) payload.dodatki = null

    const result = await articleStore.create(payload)
    // Add to picker list
    articlePickerList.value.unshift(result)
    // Auto-select the new article
    selectArticle(result)
    // Close the inline form
    showInlineArticleForm.value = false
    // Reset the form
    inlineArticleForm.value = {
      name: '', is_service: false, internal_number: '', registration_no: '',
      serial_no: '', brand: '', model: '', replacement_value: null,
      category_id: null, owner_id: null, branch_id: null,
      description: '', notes: '', rental_days: null, article_type: '',
      zasieg_m: null, udzwig_t: null, dodatki: null,
      is_archival: false, is_external: false,
    }
    catSelectedMain.value = null
    catSelectedSub1.value = null
    catSelectedSub2.value = null
  } catch (e: any) {
    inlineArticleError.value = e?.response?.data?.detail || 'Błąd zapisu artykułu'
  } finally {
    savingInlineArticle.value = false
  }
}

function selectPosition(pos) {
  selectedPosId.value = pos.id
}

// RAO-P2-071: addPosition → otwiera ArticlePicker bezpośrednio (zero modali ustawień)
function addPosition() {
  articlePickerMode.value = 'new'
  showArticlePicker.value = true
}

// RAO-P2-071: startEditPos — inline edit istniejącej pozycji (pattern jak startEditFee)
function startEditPos(pos) {
  editingPosId.value = pos.id
  clearInlinePosErrors()
  editingPosData.value = {
    article_id: pos.article_id,
    article_name: pos.article_name || '',
    rental_type: pos.rental_type ?? null,
    rental_days: pos.rental_days ?? null,
    quantity: pos.quantity ?? 1,
    unit_price: pos.unit_price ?? null,
    costs: pos.costs ?? null,
    rate_type_id: pos.rate_type_id ?? null,
    billing_frequency: pos.billing_frequency ?? null,
    billing_unit: pos.billing_unit ?? null,
    supplier_id: pos.supplier_id ?? null,
    supplier_name: pos.supplier_name || '',
    delivery_date: pos.delivery_date ?? null,
    description: pos.description ?? null,
  }
}

function cancelInlinePos() {
  editingPosId.value = null
  editingPosData.value = emptyPosData()
  clearInlinePosErrors()
}

async function saveInlinePos() {
  if (!editingPosId.value) return
  if (savingPos.value) return // RAO-P0: guard przed double-click
  if (!editingPosData.value.article_id) {
    toastStore.error('Wybierz artykuł przed zapisem')
    return
  }
  // RAO-P0: walidacja inline (quantity ≥ 1, rental_days ≥ 0)
  if (!validatePosInline(editingPosData.value)) {
    return
  }
  savingPos.value = true
  try {
    const payload = buildPosPayload(editingPosData.value)
    const updated = await contractStore.updatePosition(Number(props.id), editingPosId.value, payload)
    await contractStore.fetchPositions(Number(props.id))
    // RAO-P0: kaskada — pokaż ConditionPanel dla zapisanej pozycji
    if (updated?.id) selectedPosId.value = updated.id
    editingPosId.value = null
    editingPosData.value = emptyPosData()
    clearInlinePosErrors()
    await recalcTotal()
    toastStore.success('Pozycja zapisana')
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd zapisu pozycji')
  } finally {
    savingPos.value = false
  }
}

function cancelNewPosRow() {
  showNewPosRow.value = false
  newPosData.value = emptyPosData()
  clearInlinePosErrors()
}

async function saveNewPosRow() {
  if (savingPos.value) return // RAO-P0: guard przed double-click
  if (!newPosData.value.article_id) {
    toastStore.error('Wybierz artykuł przed zapisem')
    return
  }
  // RAO-P0: walidacja inline (quantity ≥ 1, rental_days ≥ 0)
  if (!validatePosInline(newPosData.value)) {
    return
  }
  savingPos.value = true
  try {
    const payload = buildPosPayload(newPosData.value)
    const created = await contractStore.createPosition(Number(props.id), payload)
    await contractStore.fetchPositions(Number(props.id))
    // RAO-P0: kaskada — pokaż ConditionPanel dla nowo dodanej pozycji
    if (created?.id) selectedPosId.value = created.id
    showNewPosRow.value = false
    newPosData.value = emptyPosData()
    clearInlinePosErrors()
    await recalcTotal()
    toastStore.success('Pozycja dodana')
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd dodawania pozycji')
  } finally {
    savingPos.value = false
  }
}

// Buduje payload API z inline data — nulluje puste pola opcjonalne
function buildPosPayload(d: PosInlineData) {
  const payload: Record<string, unknown> = {
    article_id: d.article_id,
    rental_type: d.rental_type || null,
    description: d.description || null,
    rental_days: d.rental_days ?? null,
    quantity: d.quantity ?? 1,
    unit_price: d.unit_price ?? null,
    costs: d.costs ?? null,
    rate_type_id: d.rate_type_id ?? null,
    billing_frequency: d.billing_frequency || null,
    billing_unit: d.billing_unit || null,
    supplier_id: d.supplier_id ?? null,
    delivery_date: d.delivery_date || null,
  }
  return payload
}

// Otwiera ArticlePicker ponownie dla istniejącej pozycji w trybie edit
function reopenArticlePickerForEdit(_pos: any) {
  articlePickerMode.value = 'edit'
  showArticlePicker.value = true
}

// Otwiera ArticlePicker dla nowego wiersza
function reopenArticlePickerForNew() {
  articlePickerMode.value = 'new'
  showArticlePicker.value = true
}

async function deletePosition(pos) {
  requestConfirm(
    `Usunąć pozycję „${pos.article_name || ''}"? Warunki rozliczeniowe tej pozycji również zostaną usunięte.`,
    async () => {
      try {
        await contractStore.deletePosition(Number(props.id), pos.id)
        if (selectedPosId.value === pos.id) selectedPosId.value = null
        await contractStore.fetchPositions(Number(props.id))
        toastStore.success('Pozycja usunięta')
      } catch (e: any) {
        toastStore.error(e.response?.data?.detail || 'Błąd usuwania pozycji')
      }
    },
    'Usuń pozycję',
    'Usuń',
  )
}

function onConditionValueChanged(_value) {
  recalcTotal()
}

// RAO-P1-015: helper — format date DD.MM from ISO string
function formatPickerDate(d: string): string {
  if (!d) return '?'
  const parts = d.split('-')
  if (parts.length === 3) return `${parts[2]}.${parts[1]}.${parts[0]}`
  return d
}

let artTimer: ReturnType<typeof setTimeout> | null = null
async function searchArticles() {
  if (artTimer) clearTimeout(artTimer)
  artTimer = setTimeout(async () => {
    const { data } = await api.get('/articles', { params: { search: articlePickerSearch.value, per_page: 50, is_service: form.value.contract_type === 'U' ? true : false } })
    articlePickerList.value = data.items.map(a => ({ ...a, _avail: null as AvailabilityResponse | null }))
    // Check availability (parallel) — RAO-P1-023 + RAO-P2-066 (z rezerwacjami)
    const excludeId = isEdit.value ? Number(props.id) : null
    await Promise.all(
      articlePickerList.value
        .filter(a => !a.is_service)
        .map(async a => {
          if (form.value.date_from && form.value.date_to) {
            await articleStore.checkAvailability(a.id, form.value.date_from, form.value.date_to, excludeId)
              .then(av => { a._avail = av as AvailabilityResponse })
              .catch(() => { a._avail = null })
          }
        })
    )
  }, 300)
}

// RAO-P2-071: selectArticle — po wyborze z ArticlePicker, dodaje pusty row (tryb new)
// lub aktualizuje article_id w istniejącym row (tryb edit). Zero modali ustawień.
async function selectArticle(a) {
  // RAO-P1-023: check availability before closing picker
  if (form.value.date_from && form.value.date_to && !a.is_service) {
    try {
      const excludeId = isEdit.value ? Number(props.id) : null
      const av = await articleStore.checkAvailability(a.id, form.value.date_from, form.value.date_to, excludeId)
      if (!av.is_available) {
        // Show conflict modal — keep picker open in background
        pendingArticle.value = a
        conflictList.value = av.conflicting_contracts ?? []
        showConflictModal.value = true
        return
      }
    } catch { /* ignore — proceed normally on error */ }
  }
  applySelectedArticle(a)
}

function applySelectedArticle(a) {
  showArticlePicker.value = false
  if (articlePickerMode.value === 'edit' && editingPosId.value !== null) {
    editingPosData.value.article_id = a.id
    editingPosData.value.article_name = a.name
  } else {
    // Tryb 'new' — ustaw artykuł w nowym wierszu i pokaż go
    newPosData.value = emptyPosData()
    newPosData.value.article_id = a.id
    newPosData.value.article_name = a.name
    newPosData.value.delivery_date = form.value.date_from || null
    showNewPosRow.value = true
    editingPosId.value = null
    nextTick(() => { newPosRentalTypeInput.value?.focus() })
  }
}

function cancelConflictSelection() {
  showConflictModal.value = false
  pendingArticle.value = null
  conflictList.value = []
}

function confirmConflictSelection() {
  showConflictModal.value = false
  showArticlePicker.value = false
  if (pendingArticle.value) {
    applySelectedArticle(pendingArticle.value)
  }
  pendingArticle.value = null
  conflictList.value = []
}

// duplicateArticle — szybkie dodanie pozycji bezpośrednio z pickera (bez inline edit)
async function duplicateArticle(a) {
  try {
    const payload = {
      article_id: a.id,
      rental_type: null,
      description: a.name || null,
      rental_days: null,
      quantity: 1,
      unit_price: null,
      costs: null,
      rate_type_id: null,
      billing_frequency: null,
      billing_unit: null,
      supplier_id: null,
      delivery_date: form.value.date_from || null,
    }
    await contractStore.createPosition(Number(props.id), payload)
    await contractStore.fetchPositions(Number(props.id))
    await recalcTotal()
    toastStore.success(`Dodano: ${a.name}`)
    // Don't close picker, keep it open for more selections
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd dodawania pozycji')
  }
}

let supTimer: ReturnType<typeof setTimeout> | null = null
// RAO-P2-071: Supplier picker dla inline edit — osobne entry dla new/edit
const supplierPickerTarget = ref<'new' | 'edit'>('new')
async function openSupplierPickerForNew() {
  supplierPickerTarget.value = 'new'
  supplierSearch.value = ''
  showSupplierPicker.value = true
  const { data } = await api.get('/contractors', { params: { per_page: 30 } })
  supplierList.value = data.items
}
async function openSupplierPickerForEdit(_pos: any) {
  supplierPickerTarget.value = 'edit'
  supplierSearch.value = ''
  showSupplierPicker.value = true
  const { data } = await api.get('/contractors', { params: { per_page: 30 } })
  supplierList.value = data.items
}

async function searchSuppliers() {
  if (supTimer) clearTimeout(supTimer)
  supTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: supplierSearch.value, per_page: 30 } })
    supplierList.value = data.items
  }, 300)
}

function selectSupplier(c) {
  if (supplierPickerTarget.value === 'edit') {
    editingPosData.value.supplier_id = c.id
    editingPosData.value.supplier_name = c.name
  } else {
    newPosData.value.supplier_id = c.id
    newPosData.value.supplier_name = c.name
  }
  showSupplierPicker.value = false
}

// Service fees — inline Excel-style CRUD
function startEditFee(fee) {
  editingFeeId.value = fee.id
  editingFeeData.value = {
    name: fee.name,
    amount_from: fee.amount_from,
    amount_to: fee.amount_to,
    unit: fee.unit || '',
    description: fee.description || '',
    is_active: fee.is_active,
    article_id: fee.article_id ?? null,
    default_price: fee.default_price ?? null,
  }
}

function cancelInlineFee() {
  editingFeeId.value = null
  editingFeeData.value = {}
}

async function saveInlineFee() {
  if (!editingFeeData.value.name) { cancelInlineFee(); return }
  try {
    const payload = { ...editingFeeData.value }
    if (!payload.unit) payload.unit = null
    if (!payload.description) payload.description = null
    await api.put(`/contracts/${props.id}/service-fees/${editingFeeId.value}`, payload)
    await contractStore.fetchServiceFees(Number(props.id))
    editingFeeId.value = null
    editingFeeData.value = {}
    toastStore.success('Usługa zapisana')
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd zapisu')
  }
}

function addFeeRow() {
  editingFeeId.value = null
  newFeeData.value = { name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true, article_id: null, default_price: null }
  showNewFeeRow.value = true
  nextTick(() => { newFeeNameInput.value?.focus() })
}

function cancelNewFeeRow() {
  showNewFeeRow.value = false
}

async function saveNewFeeRow() {
  if (!newFeeData.value.name) { cancelNewFeeRow(); return }
  try {
    const payload = { ...newFeeData.value }
    if (!payload.unit) payload.unit = null
    if (!payload.description) payload.description = null
    await api.post(`/contracts/${props.id}/service-fees`, payload)
    await contractStore.fetchServiceFees(Number(props.id))
    showNewFeeRow.value = false
    newFeeData.value = { name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true, article_id: null, default_price: null }
    toastStore.success('Usługa dodana')
  } catch (e: any) {
    toastStore.error(e.response?.data?.detail || 'Błąd dodawania')
  }
}

async function deleteServiceFee(fee) {
  requestConfirm(
    `Usunąć usługę dodatkową „${fee.name}"?`,
    async () => {
      try {
        await api.delete(`/contracts/${props.id}/service-fees/${fee.id}`)
        await contractStore.fetchServiceFees(Number(props.id))
        toastStore.success('Usługa usunięta')
      } catch (e: any) {
        toastStore.error(e.response?.data?.detail || 'Błąd usuwania')
      }
    },
    'Usuń usługę',
    'Usuń',
  )
}

async function resetServiceFees() {
  requestConfirm(
    'Zresetować usługi dodatkowe do szablonu? Obecne zostaną usunięte.',
    async () => {
      try {
        await api.post(`/contracts/${props.id}/service-fees/reset`)
        await contractStore.fetchServiceFees(Number(props.id))
        toastStore.success('Usługi zresetowane do szablonu')
      } catch (e: any) {
        toastStore.error(e.response?.data?.detail || 'Błąd resetu')
      }
    },
    'Reset usług',
    'Resetuj',
  )
}

// RAO-P1-100: szybki wybór zestawów usług dodatkowych
const dieselPreset = computed(() => presetPickerList.value.find(p => p.name && /diesel/i.test(p.name)))
const elektrykPreset = computed(() => presetPickerList.value.find(p => p.name && /elektryk|elektryczny/i.test(p.name)))
const defaultPreset = computed(() =>
  presetPickerList.value.find(p => p.is_default) ||
  presetPickerList.value.find(p => p.name && /domyślny|standardowy|default/i.test(p.name)) ||
  null
)

async function applyQuickFeePreset(kind: 'diesel' | 'elektryk' | 'default') {
  const preset = kind === 'diesel' ? dieselPreset.value : kind === 'elektryk' ? elektrykPreset.value : defaultPreset.value
  if (!preset) {
    toastStore.warning(`Nie znaleziono zestawu „${kind}" dla tego typu umowy`)
    return
  }
  await applyPreset(preset)
}

const showPresetPicker = ref(false)
const presetPickerList = ref([])
const presetPickerLoading = ref(false)
const selectedPresetId = ref<number | null>(null)

// Load presets on mount
onMounted(async () => {
  try {
    const { data } = await api.get('/settings/fee-preset-groups')
    presetPickerList.value = data.filter(p => p.contract_type === form.value.contract_type)
  } catch (e) {
    console.error('Błąd ładowania zestawów:', e)
  }
})

async function openPresetPicker() {
  showPresetPicker.value = true
  presetPickerLoading.value = true
  try {
    const { data } = await api.get('/settings/fee-preset-groups')
    presetPickerList.value = data.filter(p => p.contract_type === form.value.contract_type)
  } finally {
    presetPickerLoading.value = false
  }
}

async function applyPresetWithConfirm() {
  if (!selectedPresetId.value) return
  const preset = presetPickerList.value.find(p => p.id === selectedPresetId.value)
  if (!preset) return
  const hasFees = contractStore.serviceFees.length > 0
  const doApply = async () => {
    try {
      await api.post(`/contracts/${props.id}/service-fees/apply-preset?preset_id=${preset.id}&replace=true`)
      await contractStore.fetchServiceFees(Number(props.id))
      selectedPresetId.value = null
      toastStore.success(`Zastosowano zestaw „${preset.name}"`)
    } catch (e: any) {
      toastStore.error(e.response?.data?.detail || 'Błąd aplikowania zestawu')
    }
  }
  if (hasFees) {
    requestConfirm(
      `Zastosować zestaw „${preset.name}"? Obecne ${contractStore.serviceFees.length} pozycji zostaną zastąpione.`,
      doApply,
      'Zastosuj zestaw',
      'Zastosuj',
    )
  } else {
    await doApply()
  }
}

async function applyPreset(preset) {
  const hasFees = contractStore.serviceFees.length > 0
  const doApply = async () => {
    try {
      await api.post(`/contracts/${props.id}/service-fees/apply-preset?preset_id=${preset.id}&replace=true`)
      await contractStore.fetchServiceFees(Number(props.id))
      showPresetPicker.value = false
      toastStore.success(`Zastosowano zestaw „${preset.name}"`)
    } catch (e: any) {
      toastStore.error(e.response?.data?.detail || 'Błąd aplikowania zestawu')
    }
  }
  if (hasFees) {
    requestConfirm(
      `Zastosować zestaw „${preset.name}"? Obecne ${contractStore.serviceFees.length} pozycji zostaną zastąpione.`,
      doApply,
      'Zastosuj zestaw',
      'Zastosuj',
    )
  } else {
    await doApply()
  }
}


</script>

<style scoped>
/* RAO-P2-022: badge rozliczona */
.settled-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.settled-badge-sm {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}
.btn-success {
  background: #10b981;
  color: #fff;
  border: 1px solid #059669;
  border-radius: var(--border-radius-md, 8px);
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  transition: background 150ms;
}
.btn-success:hover { background: #059669; }
.btn-outline-danger {
  background: transparent;
  color: #dc2626;
  border: 1px solid #fca5a5;
  border-radius: var(--border-radius-md, 8px);
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  transition: all 150ms;
}
.btn-outline-danger:hover { background: #fef2f2; border-color: #dc2626; }

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-heading);
  margin: 0 0 16px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.error-message {
  color: var(--color-error);
  padding: 8px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: var(--border-radius-md);
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 500;
}
.field-error {
  display: block;
  color: var(--color-error);
  font-size: 12px;
  margin-top: 4px;
  font-weight: 500;
}
.form-control.error {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}
/* RAO-P0: walidacja inline w tabeli pozycji */
.form-control.input-error {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}
.field-error-inline {
  display: block;
  color: var(--color-error);
  font-size: 10px;
  line-height: 1.2;
  margin-top: 2px;
  font-weight: 500;
  white-space: nowrap;
}
/* RAO-P0: skeleton loader dla pozycji */
.skeleton-bar {
  display: inline-block;
  width: 120px;
  height: 10px;
  border-radius: var(--border-radius);
  background: linear-gradient(90deg, var(--color-bg-light) 25%, #e9ecef 50%, var(--color-bg-light) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
  vertical-align: middle;
  margin-right: 8px;
}
@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.address-layout {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.address-row {
  display: flex;
  gap: 8px;
}
.address-select {
  flex: 1;
}
.postal-input {
  width: 100px;
}
.city-input {
  flex: 1;
}
/* RAO-P1-008: Panel PNA — read-only info z lookup */
.pna-info-panel {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
.pna-info-title {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}
.pna-info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.pna-info-item {
  color: var(--color-text-body);
}
.pna-info-label {
  color: var(--color-text-muted);
  font-weight: var(--font-weight-medium);
}
.pna-info-sep {
  color: var(--color-border-hover);
}
.pna-error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: var(--border-radius-sm);
  padding: 6px 10px;
}
.pna-spinner {
  width: 14px;
  height: 14px;
  align-self: center;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: pna-spin 0.7s linear infinite;
}
.input-loading {
  background: var(--color-bg-light);
}
@keyframes pna-spin {
  to { transform: rotate(360deg); }
}
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  opacity: 0.6;
  transition: opacity 150ms;
}
.btn-icon:hover { opacity: 1; }
.badge-danger { background: var(--color-error-bg); color: var(--color-error); }
.form-control-xs {
  padding: 2px 6px;
  height: 28px;
  font-size: 12px;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-white);
}
.row-editing { background: var(--color-bg-editing); }
.row-editing:hover { background: var(--color-bg-editing) !important; }
.row-inactive td { opacity: 0.5; }
/* RAO-P2-071: link-button w empty state — underline on hover (design reference) */
.btn-link {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
  padding: 0;
  text-decoration: none;
}
.btn-link:hover { text-decoration: underline; opacity: 0.85; }
.btn-link:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.btn-link:active { transform: translateY(1px); }
/* RAO-P2-071: wyróżnienie wiersza w trybie inline edit — navy border */
.row-editing td {
  border-bottom: 1px solid var(--color-border);
}
.row-editing:first-child td {
  border-top: 2px solid var(--color-primary);
}

.preset-picker-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preset-picker-modal {
  background: var(--color-bg-white);
  border-radius: var(--border-radius);
  padding: var(--spacing-6);
  width: 560px;
  max-width: 95vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}
.preset-picker-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  margin-bottom: var(--spacing-4);
}
.preset-picker-card {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: 14px 16px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: border-color 150ms, box-shadow 150ms;
}
.preset-picker-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-card-hover);
}
.preset-picker-card-name {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  color: var(--color-primary);
  margin-bottom: 4px;
}
.preset-picker-card-items {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  line-height: 1.6;
}
.preset-picker-empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: var(--spacing-8) 0;
  font-size: var(--font-size-sm);
}

/* RAO-P1-100: Usługi dodatkowe */
.fee-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
  flex-wrap: wrap;
}
.fee-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.fee-header-right {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-left: auto;
  flex-wrap: wrap;
}
.fee-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.fee-preview-cell {
  font-size: var(--font-size-xs);
}
.fee-pdf-preview {
  padding: 8px 0 0 0;
  background: transparent;
}
.fee-pdf-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-bottom: 4px;
}
.fee-pdf-list {
  font-size: var(--font-size-xs);
  color: var(--color-text-body);
  line-height: 1.4;
}
.fee-pdf-line {
  margin-bottom: 1px;
}
</style>
