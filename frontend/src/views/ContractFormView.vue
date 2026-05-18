<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack">←</button>
      <span class="toolbar-info">{{ isEdit ? (contractStore.current?.number ? `Umowa: ${contractStore.current.number}` : 'Ładowanie...') : 'Nowa umowa' }}</span>
      <button v-if="isEdit" class="toolbar-btn" title="Drukuj PDF" @click="generateReport('contract')">⎙</button>
      <button v-if="isEdit" class="toolbar-btn" title="Protokół ZO" @click="generateReport('protocol_zo')">📄</button>
      <button v-if="isEdit" class="toolbar-btn" title="Przelicz wartość" @click="recalcTotal">∑</button>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area" style="padding:var(--spacing-md);overflow-y:auto;">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else style="max-width:1100px;margin:0 auto;">
        <!-- Top section: contract data -->
        <div class="page-card" style="margin-bottom:var(--spacing-md);">
          <div v-if="errorMsg" style="color:var(--color-danger);padding:8px;background:#FED7D7;border-radius:6px;margin-bottom:12px;font-size:13px;">{{ errorMsg }}</div>
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
              <label class="form-label">Data od</label>
              <input v-model="form.date_from" type="date" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Data do</label>
              <input v-model="form.date_to" type="date" class="form-control" />
            </div>
          </div>

          <div class="form-row-2" style="align-items:start;">
            <div class="form-group">
              <label class="form-label">Kontrahent *</label>
              <div style="display:flex;gap:8px;">
                <input :value="contractorName" type="text" class="form-control" disabled placeholder="Wybierz kontrahenta..." style="flex:1;" />
                <button type="button" class="btn btn-secondary btn-sm" @click="showContractorPicker = true">Wybierz</button>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Adres dostawy</label>
              <div style="display:flex;gap:8px;">
                <select v-if="contractorAddresses.length" v-model="selectedAddressId" class="form-control" style="flex:1;" @change="onAddressSelect">
                  <option :value="null">— wpisz ręcznie —</option>
                  <option v-for="addr in contractorAddresses" :key="addr.id" :value="addr.id">
                    {{ addr.name || addr.city }} — {{ addr.street || '' }} {{ addr.postal_code || '' }}
                  </option>
                </select>
                <input v-model="form.postal_code" @blur="onPostalCodeBlur" class="form-control" placeholder="00-000" style="flex:1;" maxlength="6" />
                <input v-model="form.city" class="form-control" placeholder="Miasto" style="flex:1;" />
                <textarea v-model="form.delivery_address" class="form-control" style="flex:1;" rows="2" placeholder="Uwagi dojazdowe (opcjonalnie)"></textarea>
              </div>
            </div>
          </div>

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
              <label class="form-label">Wartość (zł)</label>
              <input v-model="form.total_value" type="number" step="0.01" class="form-control" style="font-weight:700;" />
            </div>
            <div class="form-group">
              <label class="form-label">Pozostało (zł)</label>
              <input :value="remainingValue" type="text" class="form-control" disabled style="font-weight:700;color:#E53E3E;" />
            </div>
          </div>

          <div class="form-row-4">
            <div class="form-group">
              <label class="form-label">Przedpłata (zł)</label>
              <input v-model="form.prepayment_amount" type="number" step="0.01" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Dok. przedpłaty</label>
              <input v-model="form.prepayment_document" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Faktura (zł)</label>
              <input v-model="form.invoice_amount" type="number" step="0.01" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Dok. faktury</label>
              <input v-model="form.invoice_document" type="text" class="form-control" />
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa 1</label>
              <div style="display:flex;gap:8px;">
                <input v-model="form.contact_person1" type="text" class="form-control" placeholder="Imię i nazwisko" />
                <input v-model="form.contact_phone1" type="text" class="form-control" placeholder="Telefon" style="width:140px;" />
                <label class="checkbox-group" style="white-space:nowrap;"><input type="checkbox" v-model="form.show_person1" /> Drukuj</label>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa 2</label>
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
                <label class="checkbox-group"><input type="checkbox" v-model="form.report_without_data" /> Wydruk bez danych</label>
                <label class="checkbox-group"><input type="checkbox" v-model="form.hide_delivery_address" /> Ukryj adres dostawy na umowie (klient wpisze ręcznie)</label>
                <label class="checkbox-group"><input type="checkbox" v-model="form.signatures_on_page1" /> Podpisy wymagane na stronie 1</label>
                <div style="display:flex;align-items:center;gap:6px;">
                  <span style="font-size:12px;">Dni rob./tydz.:</span>
                  <input v-model.number="form.working_days_per_week" type="number" min="1" max="7" class="form-control" style="width:60px;" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Positions section -->
        <div v-if="isEdit" class="page-card" style="margin-bottom:var(--spacing-md);">
          <div style="display:flex;align-items:center;margin-bottom:12px;">
            <span class="section-title" style="margin:0;border:none;">Pozycje umowy</span>
            <button class="btn btn-primary btn-sm" style="margin-left:auto;" @click="addPosition">+ Dodaj pozycję</button>
          </div>
          <table class="data-grid">
            <thead>
              <tr>
                <th>#</th>
                <th>Artykuł</th>
                <th>Typ</th>
                <th>Dni</th>
                <th>Ilość</th>
                <th>Rozliczanie</th>
                <th>Warunki</th>
                <th>Dostawca</th>
                <th>Data dost.</th>
                <th style="width:80px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!contractStore.positions.length">
                <td colspan="10" class="empty-state">Brak pozycji</td>
              </tr>
              <tr
                v-for="(pos, idx) in contractStore.positions"
                :key="pos.id"
                :class="{ selected: selectedPosId === pos.id }"
                @click="selectPosition(pos)"
                @dblclick="editPosition(pos)"
              >
                <td>{{ idx + 1 }}</td>
                <td>{{ pos.article_name }}</td>
                <td>{{ pos.rental_type || '—' }}</td>
                <td>{{ pos.rental_days || '—' }}</td>
                <td>{{ pos.quantity || 1 }}</td>
                <td>{{ pos.billing_frequency || '—' }}</td>
                <td><span class="badge badge-info">{{ pos.conditions_count || 0 }}</span></td>
                <td>{{ pos.supplier_name || '—' }}</td>
                <td>{{ pos.delivery_date ? new Date(pos.delivery_date).toLocaleDateString('pl-PL') : '—' }}</td>
                <td>
                  <button class="btn-icon" title="Edytuj" @click.stop="editPosition(pos)">✎</button>
                  <button class="btn-icon" title="Usuń" @click.stop="deletePosition(pos)">✕</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Conditions panel for selected position -->
          <ConditionPanel
            v-if="selectedPosId && isEdit"
            :contract-id="Number(props.id)"
            :position-id="selectedPosId"
            @value-changed="onConditionValueChanged"
          />

          <!-- Service hours for service contracts (type U) -->
          <ServiceHourGrid
            v-if="selectedPosId && isEdit && form.contract_type === 'U'"
            :position-id="selectedPosId"
          />

          <!-- Service fees section -->
        <div v-if="isEdit" class="page-card">
          <div style="display:flex;align-items:center;margin-bottom:8px;">
            <span class="section-title" style="margin:0;border:none;">Usługi dodatkowe</span>
            <span style="font-size:11px;color:#718096;margin-left:12px;">Kliknij wiersz • Enter = zapisz • Esc = anuluj</span>
            <button class="btn btn-secondary btn-sm" style="margin-left:auto;margin-right:6px;" @click="openPresetPicker" title="Wybierz zestaw usług">📋 Wybierz zestaw</button>
            <button class="btn btn-secondary btn-sm" style="margin-right:8px;" @click="resetServiceFees" title="Reset do domyślnego szablonu">↻ Reset</button>
            <button class="btn btn-primary btn-sm" @click="addFeeRow">+ Dodaj</button>
          </div>
          <table class="data-grid">
            <thead>
              <tr>
                <th style="width:26%;">Nazwa</th>
                <th style="width:11%;">Kwota od</th>
                <th style="width:11%;">Kwota do</th>
                <th style="width:8%;">J.m.</th>
                <th>Opis</th>
                <th style="width:62px;">Aktywna</th>
                <th style="width:56px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!contractStore.serviceFees.length && !showNewFeeRow">
                <td colspan="7" class="empty-state">Brak usług dodatkowych — kliknij „+ Dodaj”, „💻 Wybierz zestaw” lub „↻ Reset”</td>
              </tr>
              <template v-for="fee in contractStore.serviceFees" :key="fee.id">
                <!-- EDIT MODE -->
                <tr v-if="editingFeeId === fee.id" class="row-editing">
                  <td><input v-model="editingFeeData.name" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.amount_from" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.amount_to" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td><input v-model="editingFeeData.description" class="form-control form-control-xs" @keydown.enter="saveInlineFee" @keydown.esc="cancelInlineFee" /></td>
                  <td style="text-align:center;"><input type="checkbox" v-model="editingFeeData.is_active" /></td>
                  <td>
                    <button class="btn-icon" style="color:#22543D;" title="Zapisz (Enter)" @click="saveInlineFee">✓</button>
                    <button class="btn-icon" title="Anuluj (Esc)" @click="cancelInlineFee">✕</button>
                  </td>
                </tr>
                <!-- DISPLAY MODE -->
                <tr v-else @click="startEditFee(fee)" style="cursor:pointer;" :class="{ 'row-inactive': !fee.is_active }">
                  <td>{{ fee.name }}</td>
                  <td>{{ fee.amount_from ? Number(fee.amount_from).toFixed(2) + ' zł' : '—' }}</td>
                  <td>{{ fee.amount_to ? Number(fee.amount_to).toFixed(2) + ' zł' : '—' }}</td>
                  <td>{{ fee.unit || '—' }}</td>
                  <td style="font-size:11px;">{{ formatDescription(fee.description, fee.amount_from, fee.amount_to) }}</td>
                  <td style="text-align:center;"><span :class="['badge', fee.is_active ? 'badge-success' : 'badge-muted']">{{ fee.is_active ? 'Tak' : 'Nie' }}</span></td>
                  <td>
                    <button class="btn-icon" title="Edytuj" @click.stop="startEditFee(fee)">✎</button>
                    <button class="btn-icon" title="Usuń" @click.stop="deleteServiceFee(fee)">✕</button>
                  </td>
                </tr>
              </template>
              <!-- NEW ROW -->
              <tr v-if="showNewFeeRow" class="row-editing">
                <td><input v-model="newFeeData.name" class="form-control form-control-xs" placeholder="Nazwa usługi" ref="newFeeNameInput" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.amount_from" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.amount_to" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td><input v-model="newFeeData.description" class="form-control form-control-xs" @keydown.enter="saveNewFeeRow" @keydown.esc="cancelNewFeeRow" /></td>
                <td style="text-align:center;"><input type="checkbox" v-model="newFeeData.is_active" /></td>
                <td>
                  <button class="btn-icon" style="color:#22543D;" title="Dodaj (Enter)" @click="saveNewFeeRow">✓</button>
                  <button class="btn-icon" title="Anuluj (Esc)" @click="cancelNewFeeRow">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Settlements section (RAO-P1-012) -->
        <div v-if="isEdit" class="page-card" style="margin-bottom:var(--spacing-md);">
          <div style="display:flex;align-items:center;margin-bottom:12px;">
            <span class="section-title" style="margin:0;border:none;">Rozliczenie umowy</span>
            <span style="font-size:11px;color:#718096;margin-left:12px;">Koszt klienta vs koszt firmy</span>
          </div>
          <table class="data-grid">
            <thead>
              <tr>
                <th>Pozycja</th>
                <th style="width:15%;">Koszt klienta (zł)</th>
                <th style="width:15%;">Koszt firmy (zł)</th>
                <th style="width:12%;">Marża (zł)</th>
                <th>Uwagi</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!settlements.length">
                <td colspan="5" class="empty-state">Brak danych rozliczenia — pozycje umowy pojawią się tutaj po dodaniu</td>
              </tr>
              <tr v-for="s in settlements" :key="s.id">
                <td>{{ getPositionName(s.position_id) }}</td>
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
                    {{ s.margin !== null ? Number(s.margin).toFixed(2) + ' zł' : '—' }}
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
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>NIP</th><th>Miasto</th></tr></thead>
              <tbody>
                <tr v-for="c in pickerList" :key="c.id" @click="selectContractor(c)" style="cursor:pointer;">
                  <td>{{ c.name }}</td><td>{{ c.nip || '—' }}</td><td>{{ c.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showContractorPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Preset picker modal -->
    <Transition name="modal">
      <div v-if="showPresetPicker" class="preset-picker-overlay" @click.self="showPresetPicker = false">
        <div class="preset-picker-modal">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
            <div class="preset-picker-title">Wybierz zestaw usług dodatkowych</div>
            <button class="btn-icon" style="font-size:18px;" @click="showPresetPicker = false">✕</button>
          </div>
          <div v-if="presetPickerLoading" style="text-align:center;padding:32px;color:#A0AEC0;">Ładowanie zestawów...</div>
          <div v-else-if="!presetPickerList.length" class="preset-picker-empty">
            Brak zestawów usług dla tego typu umowy ({{ form.contract_type }}).<br/>
            Dodaj zestawy w <strong>Ustawienia → Zestawy usług</strong>.
          </div>
          <div v-else>
            <div
              v-for="preset in presetPickerList"
              :key="preset.id"
              class="preset-picker-card"
              @click="applyPreset(preset)"
            >
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <div class="preset-picker-card-name">{{ preset.name }}</div>
                <div style="display:flex;gap:6px;align-items:center;">
                  <span v-if="preset.is_default" class="badge badge-muted" style="font-size:10px;">Domyślny</span>
                  <span class="badge badge-info" style="font-size:10px;">{{ preset.templates.length }} pozycji</span>
                  <button class="btn btn-primary btn-sm" style="pointer-events:none;">Zastosuj</button>
                </div>
              </div>
              <div v-if="preset.description" class="preset-picker-card-items" style="margin-top:4px;">{{ preset.description }}</div>
              <div v-if="preset.templates.length" class="preset-picker-card-items" style="margin-top:6px;">
                {{ preset.templates.slice(0, 4).map(t => t.name).join(' • ') }}{{ preset.templates.length > 4 ? ` • +${preset.templates.length - 4} więcej` : '' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Position form modal (EXTENDED with 6 missing fields) -->
    <Transition name="modal">
      <div v-if="showPosModal" class="modal-overlay" @click.self="showPosModal = false">
        <div class="modal-box" style="min-width:640px;max-height:90vh;overflow-y:auto;">
          <div class="modal-title">{{ editingPos ? 'Edycja pozycji' : 'Nowa pozycja' }}</div>
          <div class="form-group">
            <label class="form-label">Artykuł *</label>
            <div style="display:flex;gap:8px;">
              <input :value="selectedArticleName" type="text" class="form-control" disabled placeholder="Wybierz artykuł..." style="flex:1;" />
              <button type="button" class="btn btn-secondary btn-sm" @click="showArticlePicker = true">Wybierz</button>
            </div>
            <div v-if="articleAvailability !== null" style="margin-top:4px;">
              <span :class="['badge', articleAvailability ? 'badge-success' : 'badge-danger']">
                {{ articleAvailability ? 'Dostępny' : 'Wynajęty w tym okresie!' }}
              </span>
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Typ najmu</label>
              <input v-model="posForm.rental_type" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Dni najmu</label>
              <input v-model.number="posForm.rental_days" type="number" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Ilość</label>
              <input v-model.number="posForm.quantity" type="number" class="form-control" min="1" />
            </div>
            <div class="form-group">
              <label class="form-label">Cena jednostkowa (zł)</label>
              <input v-model="posForm.unit_price" type="number" step="0.01" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Koszty własne (zł)</label>
              <input v-model="posForm.costs" type="number" step="0.01" class="form-control" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label class="form-label">&nbsp;</label>
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Rozliczanie</label>
              <select v-model="posForm.billing_frequency" class="form-control">
                <option :value="null">— brak —</option>
                <option value="dziennie">dziennie</option>
                <option value="tygodniowo">tygodniowo</option>
                <option value="dwutygodniowo">dwutygodniowo</option>
                <option value="miesięcznie">miesięcznie</option>
                <option value="godzinowo">godzinowo</option>
                <option value="jednorazowo">jednorazowo</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Opłata za</label>
              <select v-model="posForm.billing_unit" class="form-control">
                <option :value="null">— brak —</option>
                <option value="doba">doba</option>
                <option value="tydzień">tydzień</option>
                <option value="miesiąc">miesiąc</option>
                <option value="godzina">godzina</option>
                <option value="sztuka">sztuka</option>
              </select>
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Typ stawki</label>
              <select v-model="posForm.rate_type_id" class="form-control">
                <option :value="null">— brak —</option>
                <option v-for="rt in settingsStore.rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Data dostawy</label>
              <input v-model="posForm.delivery_date" type="date" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Dostawca</label>
            <div style="display:flex;gap:8px;">
              <input :value="supplierName" type="text" class="form-control" disabled placeholder="Opcjonalnie wybierz dostawcę..." style="flex:1;" />
              <button type="button" class="btn btn-secondary btn-sm" @click="openSupplierPicker">Wybierz</button>
              <button v-if="posForm.supplier_id" type="button" class="btn btn-secondary btn-sm" @click="posForm.supplier_id = null; supplierName = ''">✕</button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Opis</label>
            <textarea v-model="posForm.description" class="form-control" rows="2"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showPosModal = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="savePosition" :disabled="savingPos">{{ savingPos ? '...' : 'Zapisz' }}</button>
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
              <thead><tr><th>Nazwa</th><th>Nr rej.</th><th>Marka</th><th>Typ</th><th>Dostępność</th><th style="width:80px;">Akcje</th></tr></thead>
              <tbody>
                <tr v-for="a in articlePickerList" :key="a.id" style="cursor:pointer;">
                  <td @click="selectArticle(a)">{{ a.name }}</td>
                  <td @click="selectArticle(a)">{{ a.registration_no || '—' }}</td>
                  <td @click="selectArticle(a)">{{ a.brand || '—' }}</td>
                  <td @click="selectArticle(a)"><span :class="['badge', a.is_service ? 'badge-warning' : 'badge-info']">{{ a.is_service ? 'Usługa' : 'Sprzęt' }}</span></td>
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
            <button class="btn btn-secondary btn-sm" @click="showArticlePicker = false">Anuluj</button>
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

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useContractStore } from '@/stores/contracts'
import { useContractorStore } from '@/stores/contractors'
import { useArticleStore } from '@/stores/articles'
import { useSettingsStore } from '@/stores/settings'
import ConditionPanel from '@/components/contracts/ConditionPanel.vue'
import ServiceHourGrid from '@/components/contracts/ServiceHourGrid.vue'
import api from '@/composables/useApi'

const props = defineProps({ id: String })
const router = useRouter()
const route = useRoute()
const contractStore = useContractStore()
const contractorStore = useContractorStore()
const articleStore = useArticleStore()
const settingsStore = useSettingsStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const selectedPosId = ref(null)

const form = ref({
  contractor_id: null, branch_id: null, salesperson_id: null,
  contract_type: 'S', delivery_address: '', postal_code: '', city: '', latitude: null, longitude: null, date_from: '', date_to: '',
  total_value: 0, prepayment_amount: 0, prepayment_document: '',
  invoice_amount: 0, invoice_document: '', notes: '',
  contact_person1: '', contact_phone1: '', show_person1: true,
  contact_person2: '', contact_phone2: '', show_person2: true,
  email: '', phone: '', contractor_name: '', working_days_per_week: 6, report_without_data: false, hide_delivery_address: false, signatures_on_page1: false,
})

const remainingValue = computed(() => {
  const total = Number(form.value.total_value) || 0
  const pre = Number(form.value.prepayment_amount) || 0
  const inv = Number(form.value.invoice_amount) || 0
  const remaining = total - pre - inv
  return remaining.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
})

const contractorName = ref('')
const contractorAddresses = ref([])
const selectedAddressId = ref(null)
const showContractorPicker = ref(false)
const pickerSearch = ref('')
const pickerList = ref([])

// RAO-P1-008: Auto-fill city from postal code
const onPostalCodeBlur = async () => {
  const code = form.value.postal_code.trim()
  if (!code || code.length !== 6) return
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/postal-codes/${code}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      const data = await response.json()
      form.value.city = data.city
    }
  } catch (error) {
    console.warn('Postal code lookup failed:', error)
  }
}

const showPosModal = ref(false)
const editingPos = ref(null)
const savingPos = ref(false)
const posForm = ref({ article_id: null, rental_type: '', description: '', rental_days: null, quantity: 1, unit_price: null, costs: null, rate_type_id: null, billing_frequency: null, billing_unit: null, supplier_id: null, delivery_date: null })
const selectedArticleName = ref('')
const articleAvailability = ref(null)
const showArticlePicker = ref(false)
const articlePickerSearch = ref('')
const articlePickerList = ref([])

const supplierName = ref('')
const showSupplierPicker = ref(false)
const supplierSearch = ref('')
const supplierList = ref([])

const editingFeeId = ref(null)
const editingFeeData = ref({})
const showNewFeeRow = ref(false)
const newFeeData = ref({ name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true })
const newFeeNameInput = ref(null)

// RAO-P1-012: Settlements
const settlements = ref([])


// Format description with actual amounts instead of placeholders
// Format: "{name}: {amount_from} zł - {amount_to} zł" or "{name}: {amount_from} zł ({description})"
function formatDescription(description, amount_from, amount_to) {
  if (!description) {
    // If no description, format amounts directly
    if (amount_from !== null && amount_from !== undefined) {
      const formattedFrom = Number(amount_from).toLocaleString('pl-PL', { minimumFractionDigits: 2 })
      if (amount_to !== null && amount_to !== undefined) {
        const formattedTo = Number(amount_to).toLocaleString('pl-PL', { minimumFractionDigits: 2 })
        return `${formattedFrom} zł - ${formattedTo} zł`
      }
      return `${formattedFrom} zł`
    }
    return '—'
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
  return result
}

onMounted(async () => {
  await Promise.all([
    settingsStore.fetchSalespeople(),
    settingsStore.fetchBranches(),
    settingsStore.fetchRateTypes(),
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
      await contractStore.fetchPositions(Number(props.id))
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
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Błąd zapisu'
  } finally {
    saving.value = false
  }
}

async function recalcTotal() {
  if (!isEdit.value) return
  try {
    const { data } = await api.post(`/contracts/${props.id}/recalculate`)
    form.value.total_value = data.total_value
    await contractStore.fetchOne(Number(props.id))
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd kalkulacji')
  }
}

async function generateReport(type) {
  if (!isEdit.value) return
  try {
    await contractStore.generateReport(Number(props.id), type)
  } catch (e) {
    alert('Błąd generowania raportu')
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

function getPositionName(positionId) {
  if (!positionId) return '—'
  const pos = contractStore.positions.find(p => p.id === positionId)
  if (pos) return pos.article_name || `Pozycja #${positionId}`
  return `Pozycja #${positionId}`
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
    alert('Błąd aktualizacji rozliczenia')
    // Revert to original values
    await fetchSettlements(Number(props.id))
  }
}

let pickerTimer = null
async function searchContractors() {
  clearTimeout(pickerTimer)
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

function selectPosition(pos) {
  selectedPosId.value = pos.id
}

function addPosition() {
  editingPos.value = null
  Object.assign(posForm.value, { article_id: null, rental_type: '', description: '', rental_days: null, quantity: 1, unit_price: null, costs: null, rate_type_id: null, billing_frequency: null, billing_unit: null, supplier_id: null, delivery_date: null })
  selectedArticleName.value = ''
  supplierName.value = ''
  articleAvailability.value = null
  showPosModal.value = true
}

function editPosition(pos) {
  editingPos.value = pos
  Object.assign(posForm.value, {
    article_id: pos.article_id, rental_type: pos.rental_type || '', description: pos.description || '',
    rental_days: pos.rental_days, quantity: pos.quantity || 1, unit_price: pos.unit_price, costs: pos.costs,
    rate_type_id: pos.rate_type_id, billing_frequency: pos.billing_frequency,
    billing_unit: pos.billing_unit, supplier_id: pos.supplier_id, delivery_date: pos.delivery_date,
  })
  selectedArticleName.value = pos.article_name || ''
  supplierName.value = pos.supplier_name || ''
  articleAvailability.value = null
  showPosModal.value = true
}

async function savePosition() {
  if (!posForm.value.article_id) { alert('Wybierz artykuł'); return }
  savingPos.value = true
  try {
    const payload = { ...posForm.value }
    if (!payload.delivery_date) payload.delivery_date = null
    if (editingPos.value) {
      await contractStore.updatePosition(Number(props.id), editingPos.value.id, payload)
    } else {
      await contractStore.createPosition(Number(props.id), payload)
    }
    await contractStore.fetchPositions(Number(props.id))
    showPosModal.value = false
    await recalcTotal()
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd zapisu pozycji')
  } finally {
    savingPos.value = false
  }
}

async function deletePosition(pos) {
  if (!confirm('Usunąć tę pozycję?')) return
  try {
    await contractStore.deletePosition(Number(props.id), pos.id)
    if (selectedPosId.value === pos.id) selectedPosId.value = null
    await contractStore.fetchPositions(Number(props.id))
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd')
  }
}

function onConditionValueChanged(_value) {
  recalcTotal()
}

let artTimer = null
async function searchArticles() {
  clearTimeout(artTimer)
  artTimer = setTimeout(async () => {
    const { data } = await api.get('/articles', { params: { search: articlePickerSearch.value, per_page: 50, is_service: form.value.contract_type === 'U' ? true : false } })
    articlePickerList.value = data.items.map(a => ({ ...a, _avail: null }))
    // Check availability for contract dates (parallel)
    if (form.value.date_from && form.value.date_to) {
      await Promise.all(
        articlePickerList.value
          .filter(a => !a.is_service)
          .map(async a => {
            try {
              const av = await articleStore.checkAvailability(a.id, form.value.date_from, form.value.date_to)
              a._avail = av.is_available
            } catch { a._avail = null }
          })
      )
    }
  }, 300)
}

async function selectArticle(a) {
  posForm.value.article_id = a.id
  selectedArticleName.value = a.name
  showArticlePicker.value = false
  // Check availability
  if (form.value.date_from && form.value.date_to && !a.is_service) {
    try {
      const av = await articleStore.checkAvailability(a.id, form.value.date_from, form.value.date_to)
      articleAvailability.value = av.is_available
    } catch { articleAvailability.value = null }
  } else {
    articleAvailability.value = null
  }
}

async function duplicateArticle(a) {
  // Add the article as a new position immediately
  try {
    const payload = {
      article_id: a.id,
      rental_type: '',
      description: a.name || '',
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
    // Don't close picker, keep it open for more selections
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd dodawania pozycji')
  }
}

let supTimer = null
async function openSupplierPicker() {
  supplierSearch.value = ''
  showSupplierPicker.value = true
  const { data } = await api.get('/contractors', { params: { per_page: 30 } })
  supplierList.value = data.items
}

async function searchSuppliers() {
  clearTimeout(supTimer)
  supTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: supplierSearch.value, per_page: 30 } })
    supplierList.value = data.items
  }, 300)
}

function selectSupplier(c) {
  posForm.value.supplier_id = c.id
  supplierName.value = c.name
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
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd zapisu')
  }
}

function addFeeRow() {
  editingFeeId.value = null
  newFeeData.value = { name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true }
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
    newFeeData.value = { name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true }
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd dodawania')
  }
}

async function deleteServiceFee(fee) {
  if (!confirm('Usunąć tę usługę dodatkową?')) return
  try {
    await api.delete(`/contracts/${props.id}/service-fees/${fee.id}`)
    await contractStore.fetchServiceFees(Number(props.id))
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd')
  }
}

async function resetServiceFees() {
  if (!confirm('Zresetować usługi dodatkowe do szablonu? Obecne zostaną usunięte.')) return
  try {
    await api.post(`/contracts/${props.id}/service-fees/reset`)
    await contractStore.fetchServiceFees(Number(props.id))
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd resetu')
  }
}

const showPresetPicker = ref(false)
const presetPickerList = ref([])
const presetPickerLoading = ref(false)

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

async function applyPreset(preset) {
  const hasFees = contractStore.serviceFees.length > 0
  if (hasFees && !confirm(`Zastosować zestaw „${preset.name}"? Obecne ${contractStore.serviceFees.length} pozycji zostaną zastąpione.`)) return
  try {
    await api.post(`/contracts/${props.id}/service-fees/apply-preset?preset_id=${preset.id}&replace=true`)
    await contractStore.fetchServiceFees(Number(props.id))
    showPresetPicker.value = false
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd aplikowania zestawu')
  }
}


</script>

<style scoped>
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
.badge-danger { background: #FED7D7; color: #9B2C2C; }
.form-control-xs {
  padding: 2px 6px;
  height: 28px;
  font-size: 12px;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: #fff;
}
.row-editing { background: #fffff0; }
.row-editing:hover { background: #fffff0 !important; }
.row-inactive td { opacity: 0.5; }

.preset-picker-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preset-picker-modal {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 560px;
  max-width: 95vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.preset-picker-title {
  font-size: 16px;
  font-weight: 700;
  color: #0F234E;
  margin-bottom: 16px;
}
.preset-picker-card {
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: border-color 150ms, box-shadow 150ms;
}
.preset-picker-card:hover {
  border-color: #0F234E;
  box-shadow: 0 2px 8px rgba(15,35,78,0.12);
}
.preset-picker-card-name {
  font-weight: 600;
  font-size: 14px;
  color: #0F234E;
  margin-bottom: 4px;
}
.preset-picker-card-items {
  font-size: 11px;
  color: #718096;
  line-height: 1.6;
}
.preset-picker-empty {
  text-align: center;
  color: #A0AEC0;
  padding: 32px 0;
  font-size: 13px;
}
</style>
