<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <span class="toolbar-info">Ustawienia</span>
    </div>
    <div class="content-area">
      <div style="display:grid;grid-template-columns:200px 1fr;gap:var(--spacing-md);height:100%;">
        <!-- Settings nav -->
        <div class="panel">
          <div class="panel-header">Sekcje</div>
          <div class="panel-body" style="padding:0;">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              :class="['sidebar-btn', { active: activeTab === tab.id }]"
              style="font-size:13px;padding:10px 16px;"
              @click="activeTab = tab.id"
            >{{ tab.label }}</button>
          </div>
        </div>

        <!-- Settings content -->
        <div class="panel">
          <div class="panel-header">{{ currentTabLabel }}</div>
          <div class="panel-body">

            <!-- Company tab -->
            <div v-if="activeTab === 'company'">
              <div v-if="settingsStore.loading" class="empty-state">Ładowanie...</div>
              <div v-else>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Nazwa firmy</label>
                    <input v-model="companyForm.name" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Nazwa skrócona</label>
                    <input v-model="companyForm.name_short" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">NIP</label>
                    <input v-model="companyForm.nip" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">REGON</label>
                    <input v-model="companyForm.regon" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Kod pocztowy</label>
                    <input v-model="companyForm.postal_code" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Miasto</label>
                    <input v-model="companyForm.city" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">Ulica</label>
                  <input v-model="companyForm.street" type="text" class="form-control" />
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Bank</label>
                    <input v-model="companyForm.bank_name" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Numer konta</label>
                    <input v-model="companyForm.bank_account" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Numeracja od</label>
                    <input v-model.number="companyForm.numbering_start" type="number" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Krok inkrement</label>
                    <input v-model="companyForm.increment_step" type="number" step="0.01" class="form-control" />
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">Nagłówek wydruku</label>
                  <textarea v-model="companyForm.header_text" class="form-control" rows="3"></textarea>
                </div>

                <div style="margin-top:16px;">
                  <button class="btn btn-primary" @click="saveCompany" :disabled="savingCompany">
                    {{ savingCompany ? '...' : 'Zapisz dane firmy' }}
                  </button>
                  <span v-if="companySaved" style="color:var(--color-success);margin-left:12px;font-size:13px;">✓ Zapisano</span>
                </div>
              </div>
            </div>

            <!-- Salespeople tab -->
            <div v-if="activeTab === 'salespeople'">
              <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
                <input v-model="newSp.name" type="text" class="form-control" placeholder="Imię i nazwisko" style="max-width:240px;" />
                <input v-model="newSp.phone" type="text" class="form-control" placeholder="Telefon" style="max-width:160px;" />
                <input v-model.number="newSp.commission_rate" type="number" min="0" max="100" step="0.5" class="form-control" placeholder="Prowizja %" style="max-width:110px;" />
                <button class="btn btn-primary btn-sm" @click="addSalesperson">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Nazwa</th><th>Telefon</th><th>Prowizja %</th><th>Aktywny</th><th style="width:120px;"></th></tr></thead>
                <tbody>
                  <template v-for="sp in settingsStore.salespeople" :key="sp.id">
                    <tr v-if="editingSpId === sp.id" class="row-editing">
                      <td><input v-model="editingSpData.name" class="form-control form-control-xs" @keydown.enter="saveEditSp" @keydown.esc="editingSpId = null" /></td>
                      <td><input v-model="editingSpData.phone" class="form-control form-control-xs" @keydown.enter="saveEditSp" @keydown.esc="editingSpId = null" /></td>
                      <td><input v-model.number="editingSpData.commission_rate" type="number" min="0" max="100" step="0.5" class="form-control form-control-xs" @keydown.enter="saveEditSp" @keydown.esc="editingSpId = null" /></td>
                      <td><span :class="['badge', sp.is_active ? 'badge-success' : 'badge-muted']">{{ sp.is_active ? 'Tak' : 'Nie' }}</span></td>
                      <td>
                        <button class="btn-icon" style="color:#22543D;" @click="saveEditSp" title="Zapisz">✓</button>
                        <button class="btn-icon" @click="editingSpId = null" title="Anuluj">✕</button>
                      </td>
                    </tr>
                    <tr v-else>
                      <td>{{ sp.name }}</td>
                      <td>{{ sp.phone || '—' }}</td>
                      <td>{{ sp.commission_rate != null ? sp.commission_rate + ' %' : '—' }}</td>
                      <td><span :class="['badge', sp.is_active ? 'badge-success' : 'badge-muted']">{{ sp.is_active ? 'Tak' : 'Nie' }}</span></td>
                      <td>
                        <button class="btn-icon" @click="startEditSp(sp)" title="Edytuj">✎</button>
                        <button class="btn-icon" @click="toggleSp(sp.id)" title="Przełącz">⇄</button>
                        <button class="btn-icon" @click="deleteSp(sp.id)" title="Usuń">✕</button>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <!-- Categories tab -->
            <div v-if="activeTab === 'categories'">
              <!-- Dodaj kategorię główną -->
              <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input v-model="newCat.name" type="text" class="form-control" placeholder="Nazwa kategorii głównej" style="max-width:240px;" />
                <input v-model="newCat.code" type="text" class="form-control" placeholder="Kod" style="max-width:120px;" />
                <button class="btn btn-primary btn-sm" @click="addCategory">+ Dodaj główną</button>
              </div>
              <!-- Drzewo kategorii -->
              <div v-if="settingsStore.loading" class="empty-state">Ładowanie...</div>
              <div v-else-if="settingsStore.categoriesTree.length === 0" class="empty-state">Brak kategorii</div>
              <table v-else class="data-grid">
                <thead><tr><th>Nazwa</th><th>Kod</th><th>Poziom</th><th style="width:120px;"></th></tr></thead>
                <tbody>
                  <template v-for="cat in flatCategoryTree" :key="cat.id">
                    <tr v-if="editingCatId === cat.id" class="row-editing">
                      <td :style="{ paddingLeft: (cat._depth * 20 + 8) + 'px' }">
                        <input v-model="editingCatData.name" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" />
                      </td>
                      <td><input v-model="editingCatData.code" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" /></td>
                      <td style="color:var(--color-text-secondary);font-size:11px;">{{ cat.level }}</td>
                      <td>
                        <button class="btn-icon" style="color:#22543D;" @click="saveEditCat" title="Zapisz">✓</button>
                        <button class="btn-icon" @click="editingCatId = null" title="Anuluj">✕</button>
                      </td>
                    </tr>
                    <tr v-else>
                      <td :style="{ paddingLeft: (cat._depth * 20 + 8) + 'px' }">
                        <span :style="cat._depth > 0 ? 'color:var(--color-text-secondary)' : 'font-weight:600'">
                          {{ cat._depth > 0 ? '└ ' : '' }}{{ cat.name }}
                        </span>
                      </td>
                      <td>{{ cat.code || '—' }}</td>
                      <td style="color:var(--color-text-secondary);font-size:11px;">{{ cat.level }}</td>
                      <td>
                        <button v-if="cat.level !== 'sub3'" class="btn-icon" @click="startAddSubcat(cat)" title="Dodaj podkategorię">+</button>
                        <button class="btn-icon" @click="startEditCat(cat)" title="Edytuj">✎</button>
                        <button class="btn-icon" :disabled="cat.children && cat.children.length > 0" :title="cat.children && cat.children.length > 0 ? 'Ma podkategorie' : 'Usuń'" @click="deleteCat(cat.id)">✕</button>
                      </td>
                    </tr>
                    <!-- Inline add subcategory row -->
                    <tr v-if="addingSubcatParentId === cat.id" class="row-editing">
                      <td :style="{ paddingLeft: ((cat._depth + 1) * 20 + 8) + 'px' }">
                        <input v-model="newSubcat.name" class="form-control form-control-xs" placeholder="Nazwa podkategorii" @keydown.enter="saveSubcat" @keydown.esc="addingSubcatParentId = null" autofocus />
                      </td>
                      <td><input v-model="newSubcat.code" class="form-control form-control-xs" placeholder="Kod" @keydown.enter="saveSubcat" @keydown.esc="addingSubcatParentId = null" /></td>
                      <td style="color:var(--color-text-secondary);font-size:11px;">{{ cat.level === 'main' ? 'sub1' : cat.level === 'sub1' ? 'sub2' : 'sub3' }}</td>
                      <td>
                        <button class="btn-icon" style="color:#22543D;" @click="saveSubcat" title="Zapisz">✓</button>
                        <button class="btn-icon" @click="addingSubcatParentId = null" title="Anuluj">✕</button>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <!-- Rate types tab -->
            <div v-if="activeTab === 'rate-types'">
              <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input v-model="newRt.name" type="text" class="form-control" placeholder="Nazwa typu stawki" style="max-width:300px;" />
                <button class="btn btn-primary btn-sm" @click="addRateType">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Nazwa</th><th>Opis</th><th>Zależna</th><th style="width:80px;"></th></tr></thead>
                <tbody>
                  <template v-for="rt in settingsStore.rateTypes" :key="rt.id">
                    <tr v-if="editingRtId === rt.id" class="row-editing">
                      <td><input v-model="editingRtData.name" class="form-control form-control-xs" @keydown.enter="saveEditRt" @keydown.esc="editingRtId = null" /></td>
                      <td><input v-model="editingRtData.description" class="form-control form-control-xs" @keydown.enter="saveEditRt" @keydown.esc="editingRtId = null" /></td>
                      <td style="text-align:center;"><input type="checkbox" v-model="editingRtData.is_dependent" /></td>
                      <td>
                        <button class="btn-icon" style="color:#22543D;" @click="saveEditRt" title="Zapisz">✓</button>
                        <button class="btn-icon" @click="editingRtId = null" title="Anuluj">✕</button>
                      </td>
                    </tr>
                    <tr v-else>
                      <td>{{ rt.name }}</td>
                      <td>{{ rt.description || '—' }}</td>
                      <td>{{ rt.is_dependent ? 'Tak' : 'Nie' }}</td>
                      <td>
                        <button class="btn-icon" @click="startEditRt(rt)" title="Edytuj">✎</button>
                        <button class="btn-icon" @click="deleteRt(rt.id)" title="Usuń">✕</button>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <!-- Fee preset groups tab -->
            <div v-if="activeTab === 'fee-presets'">
              <!-- new preset form -->
              <div style="display:flex;gap:8px;align-items:flex-end;margin-bottom:16px;flex-wrap:wrap;">
                <div class="form-group" style="margin:0;">
                  <label class="form-label">Typ umowy</label>
                  <select v-model="newPreset.contract_type" class="form-control" style="width:130px;">
                    <option value="S">Najem (S)</option>
                    <option value="U">Usługa (U)</option>
                  </select>
                </div>
                <div class="form-group" style="margin:0;flex:1;min-width:220px;">
                  <label class="form-label">Nazwa zestawu</label>
                  <input v-model="newPreset.name" type="text" class="form-control" placeholder="np. Standardowy, Premium…" @keydown.enter="addPreset" />
                </div>
                <div class="form-group" style="margin:0;flex:2;min-width:200px;">
                  <label class="form-label">Opis (opcjonalnie)</label>
                  <input v-model="newPreset.description" type="text" class="form-control" placeholder="Krótki opis zestawu" />
                </div>
                <button class="btn btn-primary btn-sm" @click="addPreset" style="margin-bottom:0;">+ Nowy zestaw</button>
              </div>

              <div v-if="!feePresets.length" class="empty-state">Brak zestawów — utwórz pierwszy zestaw powyżej.</div>

              <div v-for="preset in feePresets" :key="preset.id" class="preset-card">
                <div class="preset-header">
                  <div style="display:flex;align-items:center;gap:8px;">
                    <span :class="['badge', preset.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ preset.contract_type }}</span>
                    <span v-if="editingPresetId !== preset.id" style="font-weight:600;font-size:14px;">{{ preset.name }}</span>
                    <input v-else v-model="editingPresetName" class="form-control form-control-xs" style="width:260px;" @keydown.enter="savePresetName(preset)" @keydown.esc="editingPresetId = null" />
                    <span v-if="preset.is_default" class="badge badge-muted" style="font-size:10px;">Domyślny</span>
                    <span style="font-size:11px;color:#718096;">({{ preset.templates.length }} pozycji)</span>
                  </div>
                  <div style="display:flex;gap:4px;">
                    <button v-if="editingPresetId !== preset.id" class="btn-icon" title="Zmień nazwę" @click="startEditPreset(preset)">✎</button>
                    <button v-else class="btn-icon" style="color:#22543D;" title="Zapisz" @click="savePresetName(preset)">✓</button>
                    <button class="btn-icon" :class="{ active: expandedPresetId === preset.id }" title="Pokaż/ukryj pozycje" @click="toggleExpand(preset.id)">{{ expandedPresetId === preset.id ? '▲' : '▼' }}</button>
                    <button class="btn-icon" title="Usuń zestaw" @click="deletePreset(preset.id)">✕</button>
                  </div>
                </div>

                <!-- Expanded items -->
                <div v-if="expandedPresetId === preset.id" class="preset-items">
                  <table class="data-grid" style="margin-top:8px;">
                    <thead>
                      <tr>
                        <th style="width:24px;"></th>
                        <th style="width:28%;">Nazwa</th>
                        <th style="width:10%;">Cena dom.</th>
                        <th style="width:10%;">Kwota od</th>
                        <th style="width:10%;">Kwota do</th>
                        <th style="width:8%;">J.m.</th>
                        <th>Opis</th>
                        <th style="width:60px;">Aktywna</th>
                        <th style="width:64px;"></th>
                      </tr>
                    </thead>
                    <!-- Tymczasowo: prosty v-for zamiast VueDraggable do debugowania -->
                    <tbody v-if="preset.templates && preset.templates.length > 0">
                      <tr v-for="tpl in preset.templates" :key="tpl.id">
                        <template v-if="editingPresetItemId === tpl.id">
                          <!-- Edit mode -->
                          <td></td>
                          <td>
                            <!-- RAO-P1-011: Article picker instead of text input -->
                            <select v-model="editingPresetItemData.article_id" class="form-control form-control-xs" @change="onArticleSelected('edit')" style="margin-bottom:4px;">
                              <option :value="null">-- Wybierz artykuł --</option>
                              <option v-for="art in articleStore.list" :key="art.id" :value="art.id">{{ art.name }}</option>
                            </select>
                            <input v-model="editingPresetItemData.name" class="form-control form-control-xs" placeholder="Nazwa (auto z artykułu)" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" />
                          </td>
                          <td><input v-model="editingPresetItemData.default_price" type="number" step="0.01" class="form-control form-control-xs" placeholder="Cena domyślna" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.amount_from" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.amount_to" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.description" class="form-control form-control-xs" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td style="text-align:center;"><input type="checkbox" v-model="editingPresetItemData.is_active" /></td>
                          <td>
                            <button class="btn-icon" style="color:#22543D;" title="Zapisz" @click="savePresetItem(preset.id)">✓</button>
                            <button class="btn-icon" title="Anuluj" @click="editingPresetItemId = null">✕</button>
                          </td>
                        </template>
                        <template v-else>
                          <!-- Display mode -->
                          <td @click.stop title="Przeciągnij aby zmienić kolejność">⋮⋮</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer;">{{ tpl.article_name || tpl.name }}</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer;">{{ tpl.default_price ? Number(tpl.default_price).toFixed(2) + ' zł' : '—' }}</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer;">{{ tpl.amount_from ? Number(tpl.amount_from).toFixed(2) + ' zł' : '—' }}</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer;">{{ tpl.amount_to ? Number(tpl.amount_to).toFixed(2) + ' zł' : '—' }}</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer;">{{ tpl.unit || '—' }}</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer; font-size:11px;">{{ tpl.description || '—' }}</td>
                          <td @click="startEditPresetItem(tpl)" style="cursor:pointer;"><span :class="['badge', tpl.is_active ? 'badge-success' : 'badge-muted']">{{ tpl.is_active ? 'Tak' : 'Nie' }}</span></td>
                          <td>
                            <button class="btn-icon" title="Edytuj" @click.stop="startEditPresetItem(tpl)">✎</button>
                            <button class="btn-icon" title="Usuń" @click.stop="deletePresetItem(preset.id, tpl.id)">✕</button>
                          </td>
                        </template>
                      </tr>
                    </tbody>
                    <tbody v-else>
                      <tr>
                        <td colspan="9" style="text-align:center; padding: 20px; color: #718096;">
                          Brak szablonów w tym zestawie
                        </td>
                      </tr>
                    </tbody>
                    <!-- Nowy wiersz w osobnym <tbody> (HTML5 dozwala wiele tbody w tabeli) -->
                    <tbody>
                      <tr v-if="addingToPresetId === preset.id" style="background:#f0fff4;">
                        <td></td>
                        <td>
                          <!-- RAO-P1-011: Article picker for new item -->
                          <select v-model="newPresetItem.article_id" class="form-control form-control-xs" @change="onArticleSelected('new')" style="margin-bottom:4px;">
                            <option :value="null">-- Wybierz artykuł --</option>
                            <option v-for="art in articleStore.list" :key="art.id" :value="art.id">{{ art.name }}</option>
                          </select>
                          <input v-model="newPresetItem.name" class="form-control form-control-xs" placeholder="Nazwa (auto z artykułu)" ref="newPresetItemNameRef" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" />
                        </td>
                        <td><input v-model="newPresetItem.default_price" type="number" step="0.01" class="form-control form-control-xs" placeholder="Cena domyślna" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.amount_from" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.amount_to" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.description" class="form-control form-control-xs" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td style="text-align:center;"><input type="checkbox" v-model="newPresetItem.is_active" /></td>
                        <td>
                          <button class="btn-icon" style="color:#22543D;" title="Dodaj (Enter)" @click="saveNewPresetItem(preset)">✓</button>
                          <button class="btn-icon" title="Anuluj" @click="addingToPresetId = null">✕</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <button class="btn btn-secondary btn-sm" style="margin-top:8px;" @click="startAddPresetItem(preset.id)">+ Dodaj pozycję</button>
                </div>
              </div>
            </div>

            <!-- Fakturownia tab -->
            <div v-if="activeTab === 'fakturownia'">
              <div v-if="fakturowniaStore.loading" class="empty-state">Ładowanie...</div>
              <div v-else>
                <div class="form-group" style="margin-bottom:16px;">
                  <label class="form-label" style="display:flex;align-items:center;gap:8px;">
                    <input type="checkbox" v-model="fakturowniaForm.enabled" />
                    Włącz integrację Fakturownia
                  </label>
                </div>

                <div class="form-group" style="margin-bottom:16px;">
                  <label class="form-label">Subdomena Fakturownia</label>
                  <input v-model="fakturowniaForm.domain_subdomain" type="text" class="form-control" placeholder="np. toolsmart" />
                  <small style="color:var(--color-text-body);">Pełny URL: {{ fakturowniaForm.domain_subdomain }}.fakturownia.pl</small>
                </div>

                <div class="form-group" style="margin-bottom:16px;">
                  <label class="form-label">API Token</label>
                  <input v-model="fakturowniaForm.api_token" type="password" class="form-control" placeholder="Wklej token API" />
                  <div v-if="fakturowniaStore.settings?.api_token_preview" style="font-size:12px;color:var(--color-text-body);margin-top:4px;">
                    Aktualny token: {{ fakturowniaStore.settings.api_token_preview }}
                  </div>
                </div>

                <div style="margin-top:16px;">
                  <button class="btn btn-primary" @click="saveFakturowniaSettings" :disabled="fakturowniaStore.loading">
                    {{ fakturowniaStore.loading ? '...' : 'Zapisz ustawienia' }}
                  </button>
                </div>

                <div v-if="fakturowniaStore.error" style="color:var(--color-danger);margin-top:12px;padding:8px;background:#FED7D7;border-radius:6px;">
                  {{ fakturowniaStore.error }}
                </div>
              </div>
            </div>

            <!-- Folder RAO tab -->
            <div v-if="activeTab === 'folder'">
              <div style="max-width:480px;">
                <p style="color:var(--color-text-secondary);font-size:13px;margin-bottom:16px;">
                  Wybierz folder na dysku — pobrane dokumenty PDF będą automatycznie trafiać do odpowiednich podfolderów:
                  <strong>Umowy/</strong>, <strong>Protokoly/</strong>, <strong>Zestawienia/</strong>.
                  Działa w Chrome i Edge (86+). Firefox i Safari używają standardowego pobierania.
                </p>
                <div v-if="!folderApiSupported" class="empty-state" style="padding:16px;text-align:left;">
                  Twoja przeglądarka nie obsługuje File System Access API. Pliki będą pobierane standardowo.
                </div>
                <template v-else>
                  <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;padding:12px;background:var(--color-bg-subtle,#F7FAFC);border-radius:var(--border-radius,12px);border:1px solid var(--color-border,#E2E8F0);">
                    <span style="font-size:20px;">📁</span>
                    <div style="flex:1;">
                      <div style="font-size:13px;font-weight:600;color:var(--color-text);">
                        {{ folderName || 'Brak folderu' }}
                      </div>
                      <div style="font-size:11px;color:var(--color-text-secondary);">
                        {{ folderName ? 'Pliki zapisywane do: ' + folderName + '/Umowy/, /Protokoly/, /Zestawienia/' : 'Pliki pobierane standardowo (dialog przeglądarki)' }}
                      </div>
                    </div>
                  </div>
                  <div style="display:flex;gap:8px;">
                    <button class="btn btn-primary btn-sm" @click="handlePickFolder" :disabled="pickingFolder">
                      {{ pickingFolder ? '...' : folderName ? 'Zmień folder' : 'Wybierz folder RAO' }}
                    </button>
                    <button v-if="folderName" class="btn btn-secondary btn-sm" @click="handleClearFolder">
                      Usuń konfigurację
                    </button>
                  </div>
                  <div v-if="folderMsg" style="margin-top:8px;font-size:12px;" :style="{ color: folderMsgOk ? 'var(--color-success,#38A169)' : 'var(--color-danger,#E53E3E)' }">
                    {{ folderMsg }}
                  </div>
                </template>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useSettingsStore } from '@/stores/settings'
import { useArticleStore } from '@/stores/articles'
import { useFakturowniaStore } from '@/stores/fakturownia'
import api from '@/composables/useApi'
import { useTargetFolder } from '@/composables/useTargetFolder.js'

const settingsStore = useSettingsStore()
const articleStore = useArticleStore()
const fakturowniaStore = useFakturowniaStore()

const activeTab = ref('company')
const tabs = [
  { id: 'company', label: 'Dane firmy' },
  { id: 'salespeople', label: 'Handlowcy' },
  { id: 'categories', label: 'Kategorie' },
  { id: 'rate-types', label: 'Typy stawek' },
  { id: 'fee-presets', label: 'Zestawy usług dodatkowych' },
  { id: 'fakturownia', label: 'Fakturownia' },
  { id: 'folder', label: 'Folder RAO' },
]

const currentTabLabel = computed(() => tabs.find(t => t.id === activeTab.value)?.label || '')

const companyForm = ref({ name: '', name_short: '', nip: '', regon: '', postal_code: '', city: '', street: '', bank_name: '', bank_account: '', numbering_start: 1, increment_step: 50, header_text: '', logo_url: null as string | null })
const savingCompany = ref(false)
const companySaved = ref(false)

// RAO-P3-002: logo upload state
const uploadingLogo = ref(false)
const logoUploaded = ref(false)
const logoError = ref<string | null>(null)

const fakturowniaForm = ref({ enabled: false, domain_subdomain: '', api_token: '' })
const savingFakturownia = ref(false)

const newSp = ref({ name: '', phone: '', commission_rate: null })
const editingSpId = ref(null)
const editingSpData = ref({ name: '', phone: '', commission_rate: null })
const newCat = ref({ name: '', code: '', description: '' })
const newRt = ref({ name: '', description: '', is_dependent: false })

const feePresets = ref([])
const newPreset = ref({ contract_type: 'S', name: '', description: '' })
const expandedPresetId = ref(null)
const editingPresetId = ref(null)
const editingPresetName = ref('')
const editingPresetItemId = ref(null)
const editingPresetItemData = ref({})
const addingToPresetId = ref(null)
const newPresetItem = ref({ name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true, article_id: null, default_price: null })
const newPresetItemNameRef = ref(null)

// --- Folder RAO (File System Access API) ---
const { isSupported, pickFolder, clearStoredHandle, getStoredFolderName } = useTargetFolder()
const folderApiSupported = ref(isSupported())
const folderName = ref<string | null>(null)
const pickingFolder = ref(false)
const folderMsg = ref('')
const folderMsgOk = ref(true)

async function loadFolderName() {
  folderName.value = await getStoredFolderName()
}

async function handlePickFolder() {
  pickingFolder.value = true
  folderMsg.value = ''
  try {
    const result = await pickFolder()
    if (result.success) {
      folderName.value = result.folderName
      folderMsg.value = `Folder "${result.folderName}" zapisany. Pliki PDF będą trafiać do podfolderów.`
      folderMsgOk.value = true
    } else {
      folderMsg.value = 'Anulowano wybór folderu.'
      folderMsgOk.value = false
    }
  } catch {
    folderMsg.value = 'Błąd wyboru folderu.'
    folderMsgOk.value = false
  } finally {
    pickingFolder.value = false
    setTimeout(() => { folderMsg.value = '' }, 5000)
  }
}

async function handleClearFolder() {
  await clearStoredHandle()
  folderName.value = null
  folderMsg.value = 'Konfiguracja folderu usunięta.'
  folderMsgOk.value = true
  setTimeout(() => { folderMsg.value = '' }, 3000)
}

onMounted(async () => {
  await Promise.all([settingsStore.fetchAll(), settingsStore.fetchCategoriesTree()])
  const company = await settingsStore.fetchCompany()
  if (company) Object.assign(companyForm.value, company)
  await loadFeePresets()
  // RAO-P1-011: Load articles for picker
  await articleStore.fetchList({ is_service: true })
  // RAO-P3-013: Load saved folder name
  await loadFolderName()
})

async function loadFeePresets() {
  console.log('loadFeePresets: starting...');
  try {
    const { data } = await api.get('/settings/fee-preset-groups')
    console.log('loadFeePresets: API response', data);
    feePresets.value = data
    console.log('loadFeePresets: feePresets.value', feePresets.value);
  } catch (error) {
    console.error('loadFeePresets: error', error);
  }
}

async function addPreset() {
  if (!newPreset.value.name) return
  const payload = { ...newPreset.value }
  if (!payload.description) payload.description = null
  await api.post('/settings/fee-preset-groups', payload)
  await loadFeePresets()
  newPreset.value = { contract_type: newPreset.value.contract_type, name: '', description: '' }
}

async function deletePreset(id) {
  if (!confirm('Usunąć ten zestaw i wszystkie jego pozycje?')) return
  await api.delete(`/settings/fee-preset-groups/${id}`)
  if (expandedPresetId.value === id) expandedPresetId.value = null
  await loadFeePresets()
}

function toggleExpand(id) {
  expandedPresetId.value = expandedPresetId.value === id ? null : id
  addingToPresetId.value = null
}

function startEditPreset(preset) {
  editingPresetId.value = preset.id
  editingPresetName.value = preset.name
}

async function savePresetName(preset) {
  if (!editingPresetName.value) return
  await api.put(`/settings/fee-preset-groups/${preset.id}`, {
    name: editingPresetName.value,
    contract_type: preset.contract_type,
    description: preset.description,
    is_default: preset.is_default,
  })
  editingPresetId.value = null
  await loadFeePresets()
}

function startEditPresetItem(tpl) {
  editingPresetItemId.value = tpl.id
  editingPresetItemData.value = {
    name: tpl.name,
    article_id: tpl.article_id,
    default_price: tpl.default_price,
    amount_from: tpl.amount_from,
    amount_to: tpl.amount_to,
    unit: tpl.unit || '',
    description: tpl.description || '',
    is_active: tpl.is_active,
    contract_type: tpl.contract_type,
  }
}

function onArticleSelected(mode) {
  // RAO-P1-011: Auto-fill name from selected article
  const data = mode === 'edit' ? editingPresetItemData.value : newPresetItem.value
  if (data.article_id) {
    const article = articleStore.list.find(a => a.id === data.article_id)
    if (article) {
      data.name = article.name
      if (!data.default_price && article.price) {
        data.default_price = article.price
      }
    }
  }
}

async function savePresetItem(presetId) {
  if (!editingPresetItemData.value.name) return
  const payload = { ...editingPresetItemData.value }
  if (!payload.unit) payload.unit = null
  if (!payload.description) payload.description = null
  // RAO-P1-011: Send article_id and default_price
  if (!payload.article_id) payload.article_id = null
  if (!payload.default_price) payload.default_price = null
  await api.put(`/settings/fee-preset-groups/${presetId}/templates/${editingPresetItemId.value}`, payload)
  editingPresetItemId.value = null
  await loadFeePresets()
}

async function deletePresetItem(presetId, tplId) {
  if (!confirm('Usunąć tę pozycję z zestawu?')) return
  await api.delete(`/settings/fee-preset-groups/${presetId}/templates/${tplId}`)
  await loadFeePresets()
}

async function startAddPresetItem(presetId) {
  addingToPresetId.value = presetId
  newPresetItem.value = { name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true }
  await import('vue').then(({ nextTick }) => nextTick(() => newPresetItemNameRef.value?.focus()))
}

// Watch for fuel items — auto-set 200 zł default
watch(() => newPresetItem.value.name, (newName) => {
  if (!newName) return
  const lower = newName.toLowerCase()
  if ((lower.includes('tankowanie') || lower.includes('paliwo') || lower.includes('fuel')) && 
      newPresetItem.value.amount_from === null && newPresetItem.value.amount_to === null) {
    newPresetItem.value.amount_from = 200
    newPresetItem.value.amount_to = 200
    newPresetItem.value.unit = 'szt'
  }
})

async function saveNewPresetItem(preset) {
  if (!newPresetItem.value.name) return
  const payload = {
    ...newPresetItem.value,
    contract_type: preset.contract_type,
    preset_id: preset.id,
  }
  if (!payload.unit) payload.unit = null
  if (!payload.description) payload.description = null
  // RAO-P1-011: Send article_id and default_price
  if (!payload.article_id) payload.article_id = null
  if (!payload.default_price) payload.default_price = null
  await api.post(`/settings/fee-preset-groups/${preset.id}/templates`, payload)
  addingToPresetId.value = null
  await loadFeePresets()
}

async function onTemplatesReorder(preset: any): Promise<void> { // any: preset pochodzi z JSON API (dynamiczny kształt)
  const order = preset.templates.map((tpl: any, index: number) => ({
    id: tpl.id,
    sort_order: index,
  }))
  try {
    await api.patch(`/settings/fee-preset-groups/${preset.id}/templates/reorder`, { order })
  } catch (e) {
    console.error('Błąd zapisu kolejności szablonów:', e)
    await loadFeePresets()
  }
}

async function saveCompany() {
  savingCompany.value = true
  try {
    await settingsStore.updateCompany(companyForm.value)
    companySaved.value = true
    setTimeout(() => { companySaved.value = false }, 3000)
  } finally {
    savingCompany.value = false
  }
}

// RAO-P3-002: upload logo firmy
async function uploadLogo(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadingLogo.value = true
  logoUploaded.value = false
  logoError.value = null
  try {
    const result = await settingsStore.uploadLogo(file)
    companyForm.value.logo_url = result.logo_url
    logoUploaded.value = true
    setTimeout(() => { logoUploaded.value = false }, 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    logoError.value = err?.response?.data?.detail ?? 'Błąd wysyłania pliku'
    setTimeout(() => { logoError.value = null }, 5000)
  } finally {
    uploadingLogo.value = false
    // Reset input value so ten sam plik można wgrać ponownie
    input.value = ''
  }
}

async function addSalesperson() {
  if (!newSp.value.name) return
  await api.post('/settings/salespeople', newSp.value)
  await settingsStore.fetchSalespeople()
  newSp.value = { name: '', phone: '', commission_rate: null }
}

async function toggleSp(id) {
  await api.patch(`/settings/salespeople/${id}/toggle`)
  await settingsStore.fetchSalespeople()
}

async function addCategory() {
  if (!newCat.value.name) return
  await api.post('/settings/categories', { ...newCat.value, parent_id: null, level: 'main' })
  await settingsStore.fetchCategoriesTree()
  newCat.value = { name: '', code: '', description: '' }
}

async function addRateType() {
  if (!newRt.value.name) return
  await api.post('/settings/rate-types', newRt.value)
  await settingsStore.fetchRateTypes()
  newRt.value = { name: '', description: '', is_dependent: false }
}


async function deleteSp(id) {
  if (!confirm('Usunąć tego handlowca?')) return
  await api.delete(`/settings/salespeople/${id}`)
  await settingsStore.fetchSalespeople()
}

function startEditSp(sp) {
  editingSpId.value = sp.id
  editingSpData.value = { name: sp.name, phone: sp.phone || '', commission_rate: sp.commission_rate }
}

async function saveEditSp() {
  await settingsStore.updateSalesperson(editingSpId.value, editingSpData.value)
  editingSpId.value = null
}

async function deleteCat(id) {
  if (!confirm('Usunąć tę kategorię?')) return
  await settingsStore.deleteCategory(id)
  await settingsStore.fetchCategoriesTree()
}

async function deleteRt(id) {
  if (!confirm('Usunąć ten typ stawki?')) return
  await settingsStore.deleteRateType(id)
}

// Inline edit — categories
const editingCatId = ref(null)
const editingCatData = ref({ name: '', code: '', description: '' })
function startEditCat(cat) {
  editingCatId.value = cat.id
  editingCatData.value = { name: cat.name, code: cat.code || '', description: cat.description || '' }
}
async function saveEditCat() {
  if (!editingCatData.value.name) return
  await settingsStore.updateCategory(editingCatId.value, editingCatData.value)
  editingCatId.value = null
  await settingsStore.fetchCategoriesTree()
}

// Flatten tree do listy z _depth dla renderowania
const flatCategoryTree = computed(() => {
  const result: any[] = []
  function flatten(nodes: any[], depth: number) {
    for (const node of nodes) {
      result.push({ ...node, _depth: depth })
      if (node.children && node.children.length) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(settingsStore.categoriesTree, 0)
  return result
})

// Dodawanie podkategorii inline
const addingSubcatParentId = ref(null)
const newSubcat = ref({ name: '', code: '' })

function startAddSubcat(parentCat: any) {
  addingSubcatParentId.value = parentCat.id
  newSubcat.value = { name: '', code: '' }
}

async function saveSubcat() {
  if (!newSubcat.value.name || !addingSubcatParentId.value) return
  const parent = flatCategoryTree.value.find(c => c.id === addingSubcatParentId.value)
  const levelMap: Record<string, string> = { main: 'sub1', sub1: 'sub2', sub2: 'sub3' }
  const childLevel = levelMap[parent?.level] || 'sub1'
  await api.post('/settings/categories', {
    name: newSubcat.value.name,
    code: newSubcat.value.code || null,
    description: null,
    parent_id: addingSubcatParentId.value,
    level: childLevel,
  })
  addingSubcatParentId.value = null
  newSubcat.value = { name: '', code: '' }
  await settingsStore.fetchCategoriesTree()
}

// Inline edit — rate types
const editingRtId = ref(null)
const editingRtData = ref({ name: '', description: '', is_dependent: false })
function startEditRt(rt) {
  editingRtId.value = rt.id
  editingRtData.value = { name: rt.name, description: rt.description || '', is_dependent: rt.is_dependent }
}
async function saveEditRt() {
  if (!editingRtData.value.name) return
  await settingsStore.updateRateType(editingRtId.value, editingRtData.value)
  editingRtId.value = null
}

// Fakturownia settings
async function fetchFakturowniaSettings() {
  await fakturowniaStore.fetchSettings()
  if (fakturowniaStore.settings) {
    fakturowniaForm.value = {
      enabled: fakturowniaStore.settings.enabled,
      domain_subdomain: fakturowniaStore.settings.domain_subdomain || '',
      api_token: ''
    }
  }
}

async function saveFakturowniaSettings() {
  savingFakturownia.value = true
  try {
    const payload = { ...fakturowniaForm.value }
    if (!payload.api_token) {
      delete payload.api_token
    }
    await fakturowniaStore.updateSettings(payload)
    alert('Ustawienia Fakturownia zapisane')
  } catch (e: any) {
    // Error already handled in store
  } finally {
    savingFakturownia.value = false
  }
}

// Watch tab change to fetch Fakturownia settings when tab activated
watch(activeTab, async (newTab) => {
  if (newTab === 'fakturownia') {
    await fetchFakturowniaSettings()
  }
})
</script>

<style scoped>
.sidebar-btn {
  color: var(--color-text);
}
.sidebar-btn:hover {
  background: var(--color-primary);
  color: #fff;
}
.sidebar-btn.active {
  background: var(--color-primary);
  color: #fff;
  border-left: 3px solid var(--color-primary-dark, #1a3a5c);
}
.form-control-xs {
  padding: 2px 6px;
  height: 28px;
  font-size: 12px;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: #fff;
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
.row-inactive-tpl td { opacity: 0.5; }
.drag-handle { cursor: grab; user-select: none; color: #A0AEC0; padding: 0 6px; text-align: center; }
.drag-handle:active { cursor: grabbing; }
:global(.sortable-ghost) { opacity: 0.4; background: #EBF4FF; }

.preset-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
}
.preset-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f7f8ff;
  cursor: default;
}
.preset-items {
  padding: 8px 14px 14px;
  background: #fff;
}

/* RAO-P3-002: logo upload */
.logo-upload-group {
  margin-top: 16px;
}
.logo-upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.logo-preview {
  height: 48px;
  max-width: 160px;
  object-fit: contain;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 4px;
  background: var(--color-bg-white);
}
.logo-placeholder {
  height: 48px;
  width: 80px;
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #A0AEC0);
  font-size: 11px;
}
.logo-upload-btn {
  cursor: pointer;
}
.logo-file-input {
  display: none;
}
.logo-upload-status {
  font-size: 12px;
  color: var(--color-text-muted, #A0AEC0);
}
.logo-upload-ok {
  font-size: 12px;
  color: var(--color-success);
}
.logo-upload-error {
  font-size: 12px;
  color: var(--color-danger);
}
</style>
